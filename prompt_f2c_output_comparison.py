# -*- coding: utf-8 -*-
"""
Prompts for the two-phase Fortran to C++ pipeline with output comparison (no checksum):
- Phase A: Generate & stabilize SINGLE-FILE Fortran testbench (impl + program + self-check)
- Phase B: Translate to SINGLE-FILE C++ with identical test, then debug until outputs match

DEBUG / REPAIR REPLIES MUST FOLLOW THIS STRICT OUTPUT FORMAT:
  1) First line: a JSON array of short "repair intent tags", e.g.
     ["fix-braces","add-include","change-precision-double","align-seed","omp-schedule-static"]
  2) Immediately after: ONE fenced code block (```fortran or ```cpp) with the FULL single-file program
No other commentary, lines, or sections are allowed.
"""


# ===== Orchestrator instruction =====
Instruction_qer = """
You orchestrate a two-phase pipeline for Fortran to C++ code translation and verification.
PHASE A (FORTRAN BENCH FIRST):
1) Ask for a SINGLE-FILE **Fortran** program that contains:
   - the provided **Fortran implementation** (you may refactor into functions),
   - a `program` that constructs deterministic inputs (fixed sizes/seed),
   - **self-checking** that proves correctness,
   - **NO external libs** (NO GoogleTest/Catch2/etc.). OpenMP optional.
2) It must compile with `gfortran -fopenmp` (OpenMP optional) and run to completion.
3) It must produce meaningful output that can be compared with the C++ version.

PHASE B (TRANSLATE TO C++ WITH IDENTICAL TEST):
1) After Fortran passes locally, ask for a SINGLE-FILE **C++** program that:
   - implements the same logic with C++ functions,
   - **reproduces the same test scenario** (same inputs, seed, sizes),
   - produces the **SAME OUTPUT** as the Fortran program
2) If outputs mismatch or any error occurs, you will be given the logs.
   You MUST return a full single-file program in a fenced block that fixes the issue.
"""


# ===== Phase queries =====
q_generate_fortran_bench_first = """
Please produce a SINGLE-FILE Fortran program that both defines the **reference implementation**
AND contains a `program` that builds deterministic inputs and validates outputs.

CRITICAL STRUCTURE REQUIREMENTS:
- Must start with `program program_name` and end with `end program program_name`
- All variables must be declared in the program section, NOT in function/subroutine sections
- Use `implicit none` only once at the beginning
- Functions/subroutines must be defined BEFORE the main program
- No duplicate variable declarations
- NO non-standard OpenMP directives (like scan/inscan) - use only basic parallel/do/sections
- Fixed I/O format: output one scalar per line or fixed-width token sequences

Requirements:
- No external dependencies or test frameworks.
- If you use OpenMP, allow serial fallback if OpenMP is unavailable.
- Produce meaningful output that demonstrates the program's functionality
- Print results in a clear, consistent format that can be compared with C++ output
- Include numerical results, arrays, or other computational outputs

Return the entire program in a ```fortran fenced block. Nothing else.
"""

q_translate_to_cpp_same_test = """
Translate the validated Fortran program into a SINGLE-FILE **C++** program with identical logic and the **same test scenario**.
Requirements:
- Keep the same input sizes and data/seed.
- Validate results on host with the same criteria/tolerance.
- Produce the SAME output as the Fortran program
- Print results in the same format as the Fortran program
- Include the same numerical results, arrays, or computational outputs
Return the entire program in a ```cpp fenced block. Nothing else.
"""


Instruction_ser_tran = """
I now need to ask you some questions about Fortran to C++ code translation, You need to keep every answer concise.
The first question is: {Fortran_Code}
"""

Instruction_ser_unit = """
{Unit_Test_Request}
I will execute part of the unit test code you gave.
But please note that I cannot download external libraries, so please do not add any external libraries (such as google test) when writing unit testing code.
"""

delete_comments = '''Help me to delete the comments of the following Fortran code:
Fortran Code:
{Fortran_Code}
Fortran Code without comments:
'''

if_contain_ext_prompt = """
Decide if this Fortran snippet is *self‑contained* for immediate test‑bench generation.

Self‑contained means:  
1. All referenced functions / subroutines are fully defined here **or** are from the standard library.  
2. Adding a minimal `program` and standard modules lets it compile & link without unresolved symbols.  
3. No external files, network, or special hardware APIs needed.
4. If the code contains both MODULE and USE statements, the used modules must be defined in the same file.

Examples of SELF-CONTAINED code:
- A complete program with main logic
- A module that defines and uses its own subroutines/functions
- Code that only uses standard Fortran intrinsics

Examples of NOT self-contained code:
- Code that uses external modules not defined in the file
- Code that includes external files
- Code that calls undefined external functions

Return ONLY "YES" or "NO".

{Fortran_Code}
"""


# ===== Utility prompt used by the engine =====
Init_solver_prompt = """
Fortran Unit test code:
```fortran
{fortran_code}
```

C++ Unit test code:
```cpp
{cpp_code}
```
"""


# ===== Debug/repair prompts (STRICT two-part format) =====
REPAIR_TAGS_RULE = "First line = JSON array of 'repair intent tags'; then ONE fenced code block with the FULL single-file program. No other text."

combine_header_files_fortran = f"""
Your last Fortran program failed to compile or link due to missing symbols/modules.
{REPAIR_TAGS_RULE}
Return a SINGLE-FILE **Fortran** program that includes/defines EVERYTHING it needs (no external files).
Keep the same output format as the original program.
Return only a ```fortran block after the tags line.
{{compile_result}}
"""

combine_header_files_cpp = f"""
Your last C++ program failed to compile or link due to missing symbols/headers.
{REPAIR_TAGS_RULE}
Return a SINGLE-FILE **C++** program that includes/defines EVERYTHING it needs (no external files).
Keep the same output format as the original program.
Return only a ```cpp block after the tags line.
{{compile_result}}
"""

missing_terminating = f"""
Your last program contains an unterminated string literal or malformed quotes.
{REPAIR_TAGS_RULE}
Return a SINGLE-FILE fixed source file with the SAME logic and the SAME output format.
Return only the corrected code block (```fortran or ```cpp) after the tags line.
"""

ff_ct_further_modification = f"""
The **Fortran** program compiled but FAILED at runtime or produced WRONG output.
{REPAIR_TAGS_RULE}
Fix it and return a SINGLE-FILE program with meaningful output.
Return only a ```fortran block after the tags line.
{{fortran_compile_result}}
"""

ft_cf_further_modification = f"""
The **C++** program compiled but FAILED at runtime or produced WRONG / wrongly formatted output.
{REPAIR_TAGS_RULE}
Fix it and return a SINGLE-FILE program that produces the same output as the Fortran program.
Return only a ```cpp block after the tags line.
{{cpp_compile_result}}
"""

openmp_downgrade_fortran = f"""
Your last Fortran program failed due to unsupported OpenMP directives.
{REPAIR_TAGS_RULE}

COMMON OPENMP FIXES:
- Replace non-standard directives (scan/inscan) with standard parallel/do/sections
- Provide serial fallback for all OpenMP constructs
- Use only basic OpenMP features: parallel, do, sections, single, master

Return a SINGLE-FILE **Fortran** program with standard OpenMP or serial fallback.
Keep the same output format as the original program.
Return only a ```fortran block after the tags line.
{{compile_result}}
"""

openmp_downgrade_cpp = f"""
Your last C++ program failed due to unsupported OpenMP directives.
{REPAIR_TAGS_RULE}

COMMON OPENMP FIXES:
- Replace non-standard directives with standard parallel/for/sections
- Provide serial fallback for all OpenMP constructs
- Use only basic OpenMP features: parallel, for, sections, single, master

Return a SINGLE-FILE **C++** program with standard OpenMP or serial fallback.
Keep the same output format as the original program.
Return only a ```cpp block after the tags line.
{{compile_result}}
"""


# ===== Output comparison prompts =====
output_comparison_analysis = """
Compare the outputs of these two programs and determine if they produce the same results.

Fortran Program:
```fortran
{fortran_code}
```

C++ Program:
```cpp
{cpp_code}
```

Fortran Output:
{fortran_output}

C++ Output:
{cpp_output}

IMPORTANT: Focus on NUMERICAL EQUIVALENCE, not formatting differences.

Analysis criteria:
1. **Numerical values**: Are the actual numbers the same (within reasonable precision)?
2. **Logical results**: Do both programs produce the same computational results?
3. **Ignore formatting**: Ignore leading/trailing spaces, line breaks, or minor formatting differences

Examples of EQUIVALENT outputs:
- "1.00000000" vs "   1.00000000" (same number, different spacing)
- "Result: 42" vs "Result:42" (same content, different spacing)
- "1.0\n2.0" vs "1.0 2.0" (same values, different line breaks)

RESPONSE FORMAT: Start your response with either "YES" or "NO" on the first line, followed by your analysis.

Example:
YES
The outputs are numerically equivalent. Both programs calculate the same sum value of 82.5, with only minor formatting differences in the C++ output that include additional diagnostic information.
"""

output_mismatch_fix = """
The C++ program output does not match the Fortran program output. Please fix the C++ code to produce the same output as the Fortran program.

Fortran Program:
```fortran
{fortran_code}
```

C++ Program:
```cpp
{cpp_code}
```

Fortran Output:
{fortran_output}

C++ Output:
{cpp_output}

Please provide the corrected C++ code that will produce the same output as the Fortran program.
"""


# ===== Mismatch handling: test first, then implementation =====
check_and_align_test_cpp = """
You are given a validated **Fortran** program and the current **C++** program.
The C++ program must produce the SAME output as the Fortran program.

First, internally decide whether the C++ **TEST** (input construction, shapes/sizes, constants, seeds, tolerance,
and the output format) is IDENTICAL to the Fortran TEST.
- If NOT identical: Modify **ONLY THE TEST SCAFFOLD** of the C++ program so that it exactly matches the Fortran test.
  Do not change implementation yet. Keep the same output format.
- If identical: Do not change the test; modify **ONLY THE COMPUTATION** (functions and related glue)
  so that the C++ output matches the Fortran result.

Strict output format: first line = JSON array of repair intent tags; then ONE ```cpp code block with the full corrected program. No other text.
Fortran reference program:
```fortran
{fortran_code}
```
Current C++ program:
```cpp
{cpp_code}
```
"""


fix_implementation_only_cpp = """
The C++ program's test already matches the Fortran test. Do NOT change any test scaffolding (input sizes, seed, I/O, validation).
Modify ONLY the implementation/computation so that the C++ output matches the Fortran result.

Strict output format: first line = JSON array of repair intent tags; then ONE ```cpp code block with the full corrected program. No other text.
Fortran reference program:
```fortran
{fortran_code}
```
Current C++ program:
```cpp
{cpp_code}
```
"""


# ===== Decision & finishing =====
ft_ct_further_check = """
Answer only `Yes` or `No`: Do the C++ and Fortran programs produce IDENTICAL outputs?
Fortran: {fortran_compile_result}
C++: {cpp_compile_result}
"""

end_prompt_ = """
Provide the FINAL pair of programs **known to compile and run successfully** and that produce identical outputs.
Return both in two separate fenced blocks: first ```fortran, then ```cpp. No extra commentary.
"""


ff_cf_further_modification = """
modify the unit test code based on the outputs and give me the complete modified unit test code to make sure I can compile and run it directly
Fortran code result: {fortran_compile_result}
C++ code outputs: {cpp_compile_result}
"""


q_ask_s_translation = """
Here is my Fortran code: {fortran_code}. Now you need to provide a complete question (including code) to the answerer and ask him to translate this Fortran code to C++ code and give you the C++ code. Don't translate this Fortran code by yourself. Ask the answerer to follow the template to start C++ code with ```cpp and end with ```.
"""

q_ask_s_unit_test = """
Here is the answer from the solver: {ser_answer}, you now need to ask the answerer to provide the executable unit-test code for both the original Fortran code and the translated C++ code separately.

Please write the main function for both code and add the unit tests. Add them to Fortran code and C++ code separately.

In the Fortran code, you should use the following format for the unit-test checking:
if (has_close_elements(a, n, 0.8)) then
    write(*,*) "Test case 2 failed: assertion failed"
    call exit(1)
end if

In the C++ code, you should use 'assert' for the unit-test checking. One example:
assert(your_cpp_function(arg1, arg2) == expected_result);

**Important:**  
* Keep the Fortran and C++ tests completely separate—each must compile and run on its own.
* Provide one same unit-test for both Fortran and C++ code.
* The Fortran code should start with ```fortran and end with ```.
* The C++ code should start with ```cpp and end with ```.
* Each program should exit with status 0 (or print a success message) when all tests pass.

"""


further_modification_ = """
Help me continue to modify the Fortran and C++ codes to ensure that they have the same functions and provide the complete unit test code to make sure I can compile and run it directly (Not only the main code).
"""

clear_prompt_ = """
Your answer was neither 'yes' nor 'no'. Please provide a clear answer.
"""

Prompts_Fortran_to_Cpp = '''Help me to translate the following Fortran code to C++ code, don't give any words: 
Fortran Code: 
program DRB093_doall2_collapse_orig_no
 use omp_lib
 use DRB093
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel do collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end parallel do
end program
Translated C++ Code: #include <stdio.h>
int a[100][100];
int main()
{
 int i,j;
#pragma omp parallel for collapse(2)
 for (i=0;i<100;i++)
 for (j=0;j<100;j++)
 a[i][j]=a[i][j]+1;
 return 0;
}

Help me to translate the following Fortran code to C++ code, don't give any words: 
Fortran Code: 
program DRB096_doall2_taskloop_collapse_orig_no
 use omp_lib
 use DRB096
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel
 !$omp single
 !$omp taskloop collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end taskloop
 !$omp end single
 !$omp end parallel

 print 100, a(50,50)
 100 format ('a(50,50) =',i3)

end program. 
Translated C++ Code: #include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];
int main()
{
 int i, j;
#pragma omp parallel
 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Help me to translate the following Fortran code to C++ code, don't give any words: 
Fortran Code:
{Fortran_Code}
Translated C++ Code:
'''

prompts_f2c_func_expl = '''Help me to translate the following Fortran code to C++ code by using the following format:
The function of the source Fortran Code is: ...
Translated c++ code is: ...
Explanation: ...

Example:
Fortran Code needs to be translated:
program DRB093_doall2_collapse_orig_no
 use omp_lib
 use DRB093
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel do collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end parallel do
end program
Translated C++ Code: #include <stdio.h>
int a[100][100];
int main()
{
 int i,j;
#pragma omp parallel for collapse(2)
 for (i=0;i<100;i++)
 for (j=0;j<100;j++)
 a[i][j]=a[i][j]+1;
 return 0;
}

The function of the source Fortran Code is: 
The original Fortran code is designed to initialize a two-dimensional array and then increment each element in the array by 1. It does this in parallel using OpenMP, a standard for parallel programming. The collapse(2) directive is used to flatten the nested loop structure into a single iteration space, allowing for more efficient parallel execution.

Translated c++ code is: 
#include <omp.h>
#include <iostream>

int main() {
    const int len = 100;
    int a[len][len];

    #pragma omp parallel for collapse(2)
    for (int i = 0; i < len; i++) {
        for (int j = 0; j < len; j++) {
            a[i][j] = a[i][j] + 1;
        }
    }

    return 0;
}

Explanation: 
1. Header Files: The C++ code includes <omp.h> for OpenMP support and <iostream> for input/output operations, although the latter is not used in this snippet. In contrast, the Fortran code uses omp_lib module for OpenMP and a custom module DRB093, which is not used in the snippet provided.
2. Array Initialization: The C++ code statically declares a 2D array a[100][100]. In the Fortran code, the array a is dynamically allocated with dimensions [len][len], where len = 100. C++ code assumes the array is globally initialized to zeroes, similar to what would happen by default in Fortran.
3. Parallel Region: The C++ code uses #pragma omp parallel for collapse(2) to parallelize the nested loop. This is directly analogous to the Fortran version's !$omp parallel do collapse(2), indicating that both loops are collapsed into a single parallel loop.
4. Loop Indices: Fortran arrays are 1-indexed, while C++ arrays are 0-indexed. Therefore, the loop in C++ starts from 0 up to len-1, whereas in Fortran, it goes from 1 to len. This difference is accounted for in the translation.
5. Increment Operation: The core operation inside the loops, a[i][j] = a[i][j] + 1, remains the same in both languages, incrementing each element of the array by 1.
This translation maintains the original code's intent and structure, adjusting for the syntactic and indexing differences between Fortran and C++.

Real Code:
Fortran Code needs to be translated:
{Fortran_Code}
'''

Asserter_Y_N = '''
I will provide you a paragraph of Fortran code and a paragraph of translated C++ code, you need to help me to assess if they perform the same function. You only need to tell me whether this Fortran code has been correctly translated into C++ code. If it is, just answer: "Yes". If not, answer: "No", and provide the reason.
Fortran code:
program DRB093_doall2_collapse_orig_no
 use omp_lib
 use DRB093
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel do collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end parallel do
end program
Translated C++ Code: 
#include <stdio.h>
int a[100][100];
int main()
{
 int i,j;
#pragma omp parallel for collapse(2)
 for (i=0;i<100;i++)
 for (j=0;j<100;j++)
 a[i][j]=a[i][j]+1;
 return 0;
}

Answer: Yes

Fortran code:
program DRB096_doall2_taskloop_collapse_orig_no
 use omp_lib
 use DRB096
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel
 !$omp single
 !$omp taskloop collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end taskloop
 !$omp end single
 !$omp end parallel

 print 100, a(50,50)
 100 format ('a(50,50) =',i3)

end program. 
Translated C++ Code: 
#include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];

 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Answer: No
1.The C++ code is missing the declaration and initialization of the loop variables i and j.
2.The C++ code has unnecessary double curly braces ({{ and }}).
3.The C++ code is missing the #pragma omp parallel directive before the #pragma omp single.

Fortran code:
{Fortran_Code}
Translated C++ Code:
{Cpp_Code}
Answer:
'''

Own_model_Modify_code = '''
The following code translation is not perfect, you need to modify the translated C++ Code based on the reasons.
Original Fortran code:
{Fortran_Code}
Translated C++ Code:
{Cpp_Code}
Reasons:
{Reasons}
Modified C++ Code:
'''

Own_model_Y_N =  '''Help me to assess if the translated C++ is correct. 
                  Source fortran code: {Fortran_code}
                  Translated C++ Code: {Cpp_code}
                  Answer:'''


Prompts_Fortran_to_Cpp_modify = '''Help me to modify the translated C++ code based on the reason above, just provide the modified C++ code, don't give any words: 
C++ Code: #include <stdio.h>
int a[100][100];
int main()
{
 int i,j;
#pragma omp parallel for collapse(2)
 for (i=0;i<100;i++)
 for (j=0;j<100;j++)
 a[i][j]=a[i][j]+1;
 return 0;
}

Help me to modify the translated C++ code based on the reason above, just provide the modified C++ code, don't give any words: 
C++ Code: #include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];
int main()
{
 int i, j;
#pragma omp parallel
 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Help me to modify the translated C++ code based on the reason above, just provide the modified C++ code, don't give any words: 
C++ Code:
'''

Compiler_inital_prompt_ = '''I am trying to translate a paragraph of Fortran code to C++ code, but the translated C++ code cannot pass the compiler.  
Please modify the C++ code so that it compiles successfully.  
**Return only the modified C++ code—no explanations.**

Source Fortran Code:
program DRB096_doall2_taskloop_collapse_orig_no
 use omp_lib
 use DRB096
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel
 !$omp single
 !$omp taskloop collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end taskloop
 !$omp end single
 !$omp end parallel

 print 100, a(50,50)
 100 format ('a(50,50) =',i3)

end program. 

Translated C++ Code:
#include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];

 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Modified C++ Code:
#include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];
int main()
{
 int i, j;
#pragma omp parallel
 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Source Fortran Code:
{Fortran_Code}
Translated C++ Code:
{Cpp_Code}
Modified C++ Code:
'''

Compiler_inital_prompt = '''I am trying to translate a paragraph of Fortran code to C++ code, but the translated C++ code cannot pass the compiler.  
Please modify the C++ so it **compiles successfully**.  
Return **only** the modified C++ code—no explanations.

Source Fortran Code:
program DRB096_doall2_taskloop_collapse_orig_no
 use omp_lib
 use DRB096
 implicit none

 integer :: len, i, j
 len = 100

 allocate (a(len,len))

 !$omp parallel
 !$omp single
 !$omp taskloop collapse(2)
 do i = 1, len
 do j = 1, len
 a(i,j) = a(i,j)+1
 end do
 end do
 !$omp end taskloop
 !$omp end single
 !$omp end parallel

 print 100, a(50,50)
 100 format ('a(50,50) =',i3)

end program. 

Translated C++ Code:
#include <stdio.h>
#if (_OPENMP<201511)
#error "An OpenMP 4.5 compiler is needed to compile this test."
#endif

#include <stdio.h>
int a[100][100];

 {
#pragma omp single
 {
#pragma omp taskloop collapse(2)
 for (i = 0; i < 100; i++)
 for (j = 0; j < 100; j++)
 a[i][j]+=1; 
 }
 }
 printf ("a[50][50]=%d\n", a[50][50]);
 return 0;
}

Source Fortran Code:
{Fortran_Code}
Translated C++ Code:
{Cpp_Code}
'''

Compiler_check_prompt = '''
The compiler is throwing errors. The error report is: {reason}. Please help me to continue modifying the C++ code. Just write out the modified C++ code based on the error report, DO NOT write other words! New C++ Code:
'''

Unit_Test_prompt = '''
I want you to help me choose suitable code for a unit test. I will provide
two snippets: one in Fortran and one in C++.

Tasks
-----
1. Check whether the two snippets have the same value‑based input and output parameters.
2. If they do not, reply "False".
3. If they do, output a Google‑Test skeleton of the form

TEST(MyLib, MyKernel_test) {
    // ---- prepare identical inputs ----
    /* ... */

    // ---------- C++ reference ----------
    cpp_function_name(/* host args */);

    // ---------- Fortran function call ----------
    /* call Fortran function with same inputs */

    EXPECT_EQ(/* C++ result */, /* Fortran result */);
}

Notes
-----
* Wrap literal braces in your output as double braces {{ }} so they are not interpreted as format placeholders.
* When calling the Fortran function, use the appropriate calling convention.
* Use EXPECT_EQ, EXPECT_FLOAT_EQ, or EXPECT_NEAR as appropriate.

Examples
========

Example 1 -> False
------------------
Fortran code:
program badIndex
    real :: a(10)
    integer :: i
    i = 1.5  ! illegal float index
    a(i) = 0.0
end program

C++ code:
int main() {
    float a[10];
    a[1] = 0.0f;
    return 0;
}

Answer:
False

Example 2 -> Unit‑test skeleton
-------------------------------
Fortran code:
subroutine saxpy(n, a, x, y)
    integer :: n
    real :: a
    real, dimension(n) :: x, y
    integer :: i
    
    do i = 1, n
        y(i) = a * x(i) + y(i)
    end do
end subroutine saxpy

C++ code:
void saxpy_cpu(int n, float a, const float* x, float* y) {
    for (int i = 0; i < n; ++i) {
        y[i] = a * x[i] + y[i];
    }
}

Answer:
TEST(SaxpyLib, Saxpy_test) {
    const int N = 1024;
    const float A = 2.0f;
    float hx[N], hy_cpp[N], hy_fortran[N];

    for (int i = 0; i < N; ++i) {
        hx[i]      = static_cast<float>(i);
        hy_cpp[i]  = static_cast<float>(i * 0.5f);
        hy_fortran[i] = hy_cpp[i];
    }

    saxpy_cpu(N, A, hx, hy_cpp);  // C++ reference

    // Call Fortran function (assuming it's compiled and linked)
    saxpy_(&N, &A, hx, hy_fortran);

    for (int i = 0; i < N; ++i) {
        EXPECT_FLOAT_EQ(hy_cpp[i], hy_fortran[i]);
    }
}

Example 3 -> no code provided
-----------------------------
Fortran code:

C++ code:

Answer:


Real code
---------
Fortran code:
{fortran_code}

C++ code:
{cpp_code}

Answer:
'''

modify_code = """Please modify the code and give the modified complete code, make sure all the functions are within a file and I will re-run the code.
1. You can add debugging statements if needed.
2. If there is a need for external library installations, please let me know the appropriate pip command by enclosing them in ```sh ```"""

check_correctness = "Please judge whether the test code you just gave is correct based on the output of the code execution. Just Answer: 'Yes' or 'No'. "

end_dialogue = """
Give me the correct modified function code (without the test code) based on your last unit test code.
"""

further_modification = """
Please go ahead and modify the code to make sure it can run correctly.
You should make sure all the functions are within a file and I will re-run the code.
"""

start_prompt = """
Could you help verify whether your code can run correctly?
1. If needed, You could create some mock data or files to assist with this. But note that whether you create new data or create a new file and write the data to it, these operations need to be done in same python file.
2. I will help you to install the related packages, you just need to tell me how install the package you need by using ```sh ... ```.
3. Our goal is to verify that the function works correctly. So you need to make sure you provide me with a complete python code rather than providing some simplified version of it.
"""

run_code_prompt = """
To confirm the code functions properly, we should execute it and check its performance.
Let's test the code to make sure it operates as expected.
To verify that the code is functioning correctly, let's run a test.
Let's execute the code to validate its proper functioning.
To make certain our code is running right, we should perform a test.
Let's initiate a run to confirm that the code works as intended.
To ascertain the code's effectiveness, we must test it.
We need to run the code to ensure it meets our standards.
Let's check the code's functionality by running it.
To guarantee the code's accuracy, testing it is essential.
We should execute the code to verify its accuracy.
Let's run the code to make sure everything is functioning properly.
To ensure flawless operation, we need to test the code.
Let's operate the code to check its effectiveness.
We should validate the code's performance by running it.
Let's put the code through a run-test to ensure it works correctly.
To be certain of the code's operation, we need to run it.
Running the code will help us verify its proper function.
Let's test run the code to check for any issues.
To confirm code reliability, let's execute it now.
We should run a trial to test the code's functionality.
Let's activate the code to ensure it's working as it should.
Running the code will confirm its efficiency and correctness.
We need to execute the code to confirm that it performs correctly.
To make sure the code is error-free, let's run a verification test.
Let's run the code to determine if it functions correctly.
We should check the code by running it to ensure its efficacy.
Let's perform a test run to validate the code's functionality.
To ascertain code performance, executing it is necessary.
We must run the code to ensure it operates efficiently.
To verify the code's success, let's give it a run.
Running the code will allow us to confirm its functionality.
We need to execute the code to see if it's working properly.
Let's initiate a test run to ensure the code is effective.
To confirm the code's operational success, testing it is crucial.
Let's deploy the code to check its working condition.
Running the code is essential to verify its proper execution.
We should operate the code to confirm its capabilities.
Let's activate a test run to ensure the code functions well.
To make sure the code performs its intended functions, we need to run it.
Running the code will help us ensure it meets functional requirements.
We should test the code to confirm that it executes properly.
Let's perform a functional test to ensure the code is running correctly.
To check the code's precision, let's run it.
We must initiate a test to verify the code's functionality.
To determine if the code is error-free, we should run it now.
Running the code is the best way to ensure its accuracy.
Let's conduct a run to verify that the code operates as it should.
We need to run the code to check its functionality and reliability.
Let's execute the code to test its overall performance.
"""

verify_code_prompt = """
Can you check if your code runs as expected?
Could you test your code to see if it functions properly?
Would you mind confirming that your code operates correctly?
Can you please verify the functionality of your code?
Could you ensure that your code is executing correctly?
Would you verify whether your code is functioning properly?
Can you determine if your code performs well?
Could you assist in checking if your code runs smoothly?
Can you help confirm your code's correctness?
Would you be able to test if your code is working right?
Can you examine your code to ensure it operates as intended?
Could you validate that your code works properly?
Would you mind running a test on your code to verify its performance?
Can you see if there are any issues with how your code runs?
Could you take a look to confirm your code functions correctly?
Would you mind ensuring your code's accuracy?
Can you help determine if your code is error-free?
Could you check for any flaws in your code's operation?
Would you be able to confirm the operational functionality of your code?
Can you make sure that your code is free of errors?
Could you perform a quick check to see if your code runs correctly?
Would you test your code to ensure it's executing properly?
Can you verify that your code meets the expected standards?
Could you assist by verifying your code's performance?
Would you mind checking if your code executes without issues?
Can you confirm the reliability of your code?
Could you please ensure that your code works as it should?
Would you assess whether your code runs effectively?
Can you help verify your code's operational correctness?
Could you double-check the functioning of your code?
Would you mind verifying that your code operates without problems?
Can you look into whether your code functions as planned?
Could you help confirm that your code performs as needed?
Would you be willing to check your code for proper operation?
Can you ensure that your code executes as expected?
Could you run a diagnostic to see if your code is working correctly?
Would you mind testing your code for functionality?
Can you verify the accuracy of your code's execution?
Could you provide assurance that your code is running properly?
Would you verify if your code is up to performance standards?
Can you check your code for any operational errors?
Could you run a trial on your code to confirm it functions correctly?
Would you conduct a check to ensure your code is accurate?
Can you help make sure your code is functioning correctly?
Could you assess if your code is performing as expected?
Would you mind giving your code a run-through to check its correctness?
Can you verify if your code is functioning up to standards?
Could you please test your code for correct operation?
Would you be willing to help ensure that your code is running smoothly?
Can you confirm if your code meets all functional requirements?
Make sure the code runs as intended.
Ensure that the code functions properly.
Verify the correct operation of the code.
Confirm that the code performs as expected.
Double-check the execution of the code.
Test the code to see that it works correctly.
Ascertain that the code behaves as it should.
Check that the code operates correctly.
Ensure the code executes without errors.
Validate the functionality of the code.
Review the code's performance to ensure accuracy.
Monitor the execution to confirm it's functioning properly.
Examine the code to make sure it runs smoothly.
Assess whether the code meets the expected outcomes.
Certify that the code is executing as planned.
Scrutinize the code for proper execution.
Check off that the code works as designed.
Inspect the code for correct operation.
Reconfirm that the code operates as intended.
Authenticate the correct running of the code.
Proof the code to ensure it's working correctly.
Cross-verify the execution of the code.
Make certain the code is functioning correctly.
Confirm the proper execution of your code.
Ensure your code executes as planned.
Verify that your code runs correctly.
Double-check that your code is functioning properly.
Make sure your code performs as expected.
Check that your code operates smoothly.
Validate that your code meets the operational criteria.
Ensure the code does what it's supposed to do.
Test to ensure the code's functionality.
Confirm that the code is error-free upon execution.
Ensure that the code delivers the expected results.
Double-check the code's results for accuracy.
Confirm that the code's output is as anticipated.
Make sure the code completes without issues.
Ensure that the code's performance is up to standard.
Confirm the reliability of the code during execution.
Make sure the code's logic performs correctly.
Verify the outcome of the code's execution.
Check for any discrepancies in the code's operation.
Ensure the code executes as it is supposed to.
Confirm the stability of the code upon execution.
Test the code thoroughly before finalizing.
Make certain the code executes without any hiccups.
Validate the precision of the code's operation.
Check that the code complies with the requirements.
Recheck the code's functionality for assurance.
Ensure that the code achieves the intended functionality.
Monitor the code to ensure it executes flawlessly.
Evaluate the code's execution to confirm correctness.
Ascertain that the code meets performance standards.
Review the code to ensure it fulfills its purpose.
Confirm that the code executes according to the plan.
Make sure the code is free from execution errors.
Ensure that the code's execution aligns with expectations.
Cross-check to confirm the code's proper functionality.
Validate that the code operates as it should.
Confirm that the code's process is correct.
Make certain the code's results are accurate.
Ensure that the code runs efficiently.
Verify that the code's performance is satisfactory.
Check that the code is functioning as it should.
Test the code's execution for any potential issues.
Make sure the code functions as intended under all conditions.
Confirm the integrity of the code's operations.
Ensure that the code performs effectively.
Review the code execution for any anomalies.
Validate the effectiveness of the code's execution.
Double-check the code for flawless performance.
Ensure that the code meets all operational expectations.
Confirm that the code handles all scenarios correctly.
Verify the code's effectiveness in real conditions.
Check the code's consistency in execution.
Make certain that the code adheres to the expected behavior.
Ensure the code's compliance with the specifications.
Confirm the code's capability to perform as necessary.
Monitor the code's performance for stability.
Ascertain that the code is ready for deployment.
Make sure the code satisfies all functional requirements.
Ensure that the code executes without deviations.
Confirm the code's readiness for operational use.
Test the code for dependability during execution.
Verify the code's robustness in various environments.
Check that the code performs efficiently.
Confirm that the code is up to professional standards.
Ensure the code's operations are in full effect.
Reaffirm the code's readiness for live environments.
Make sure the code is optimized for performance.
Confirm the code's suitability for the intended tasks.
Double-check the code for operational accuracy.
Ensure the code meets the quality standards.
Verify the code's readiness for full-scale use.
Confirm that the code maintains consistency.
Make certain the code delivers on its promises.
Ensure the code's functionality before release.
Confirm that the code functions optimally.
Double-check to ensure the code's successful execution.
Make sure the code's behavior matches the documentation.
"""

final_code_prompt = """
Our code has passed all the tests successfully, here's the code:
The code has successfully cleared all the tests, here it is:
We've successfully passed all tests with our code, here's the code:
All tests have been successfully passed by our code, here is what we wrote:
Our program succeeded in all the tests, here's the code:
Our code has cleared all its tests successfully, here's the code:
We've completed all tests successfully, here's our code:
Our coding tests were all passed successfully, here's our code:
Every test has been successfully passed by our code, see it here:
Our code achieved success in all the tests, here it is:
Successfully, our code has passed all tests, here's what we developed:
Our code met all the test criteria successfully, here is the code:
Our code excelled in all the tests, here's the code:
All the tests have been cleared by our code, here it is:
Our software has successfully passed all the testing, here's the code:
Every test was a success for our code, here's the code:
We've passed all the required tests with our code, here it is:
Our code was successful in all the tests, here is our work:
The tests were all successfully passed by our code, here it is:
Our code sailed through all the tests, here's the code:
Our code has surpassed all testing successfully, here it is:
We've successfully navigated all tests with our code, here's the result:
All required tests were successfully passed by our code, see it here:
Our code has triumphed in all the tests, here's our code:
Every test has been successfully conquered by our code, here it is:
Our application passed all tests successfully, here is the code:
The code has proven successful in all tests, here it is:
Our code has come through all the tests with success, here's the code:
Our programming successfully passed all examinations, here's our code:
We've mastered all the tests with our code, here it is:
Our system has successfully passed all tests, here is the code:
The code has been successful in all tests, here is our work:
Every testing hurdle was successfully cleared by our code, here it is:
We've cleared all tests with our code successfully, here's the code:
Our code has been vetted and succeeded in all tests, here it is:
All tests have been met with success by our code, here's the code:
Our project successfully passed all the test phases, here is our code:
Successfully, our code has conquered all the tests, here's the output:
Our code managed to pass all tests successfully, here's the code:
The code has fulfilled all test conditions successfully, here it is:
Our code was tested and passed all assessments successfully, here's the code:
Every test was smoothly passed by our code, here's what we coded:
Our code nailed all the tests successfully, here's our work:
We have successfully completed all tests with our code, here it is:
Every test criteria was met successfully by our code, here's the code:
Our script passed all tests without fail, here is the code:
Our code stood up to all tests and passed, here's the code:
All testing barriers were successfully broken by our code, here it is:
Our code has flawlessly passed all the tests, here's our script:
Our code has been validated through all tests successfully, here's the code:
"""
