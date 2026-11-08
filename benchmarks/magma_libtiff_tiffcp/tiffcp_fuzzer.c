#ifdef FRCOV
#define FIXREVERTER_SIZE 412
short FIXREVERTER[FIXREVERTER_SIZE];
#endif
/* libFuzzer wrapper for Magma's command-line drivers (tiffcp, xmllint).
 * Magma runs the tool once per input as `<tool> <ARGS with @@ = input file>`. This harness does the same
 * in-process: the tool is compiled with -Dmain=fr_tool_main -Dexit=fr_tool_exit, the input is written to a
 * temp file, getopt state is reset, and exit() returns to the harness via longjmp.
 * Build with -DFR_TOOL_ARGS='"arg1","@@",...' (the Magma *_ARGS, split into words). */
#include <setjmp.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int fr_tool_main(int argc, char **argv);
static jmp_buf fr_env;
static int fr_in_tool;
void fr_tool_exit(int code) {
  if (fr_in_tool) longjmp(fr_env, 1);
  _Exit(code);
}

#ifdef FRCOV
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  
  #ifdef FRCOV
  char *fixReverterEnv = getenv("FIXREVERTER");
  char *fixReverterToken = strtok(fixReverterEnv, " ");
  if (fixReverterToken == NULL) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 1;
  } else if (!strcmp("on", fixReverterToken)) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 0;
    fixReverterToken = strtok(NULL, " ");
    while (fixReverterToken != NULL) {
      FIXREVERTER[atoi(fixReverterToken)] = 1;
      fixReverterToken = strtok(NULL, " ");
    }
  } else if (!strcmp("off", fixReverterToken)) {
    for (int i = 0; i < FIXREVERTER_SIZE; i++)
      FIXREVERTER[i] = 1;
    fixReverterToken = strtok(NULL, " ");
    while (fixReverterToken != NULL) {
      FIXREVERTER[atoi(fixReverterToken)] = 0;
      fixReverterToken = strtok(NULL, " ");
    }
  } else {
    fprintf(stderr, "[FIXREVERTER] - first token must be on or off\n");
    exit(0);
  }
  #endif
  char in[] = "/tmp/fr_cli_in_XXXXXX";
  int fd = mkstemp(in);
  if (fd < 0) return 0;
  if (size && write(fd, data, size) != (ssize_t)size) { close(fd); unlink(in); return 0; }
  close(fd);
  char out[64];
  snprintf(out, sizeof out, "/tmp/fr_cli_out_%d", (int)getpid());
  const char *tmpl[] = {"tool", FR_TOOL_ARGS, NULL};
  char *argv[32];
  int argc = 0;
  for (; tmpl[argc] && argc < 31; argc++) {
    if (!strcmp(tmpl[argc], "@@")) argv[argc] = in;
    else if (!strcmp(tmpl[argc], "tmp.out")) argv[argc] = out;
    else argv[argc] = (char *)tmpl[argc];
  }
  argv[argc] = NULL;
  optind = 1; opterr = 0;
  fr_in_tool = 1;
  if (!setjmp(fr_env)) fr_tool_main(argc, argv);
  fr_in_tool = 0;
  unlink(in); unlink(out);
  return 0;
}
