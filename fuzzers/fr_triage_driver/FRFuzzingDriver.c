#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>

#define MAX_FILE (1 * 1024 * 1024L)

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size);

static int ExecuteFilesOnyByOne(int argc, char **argv) {

  unsigned char *buf = (unsigned char *)malloc(MAX_FILE);

  for (int i = 1; i < argc; i++) {

    int fd = 0;

    if (strcmp(argv[i], "-") != 0) { fd = open(argv[i], O_RDONLY); }

    if (fd == -1) { continue; }

    ssize_t length = read(fd, buf, MAX_FILE);

    if (length > 0) {

      printf("Reading %zu bytes from %s\n", length, argv[i]);
      LLVMFuzzerTestOneInput(buf, length);
      printf("Execution successful.\n");

    }

    if (fd > 0) { close(fd); }

  }

  free(buf);
  return 0;

}

int main(int argc, char **argv) {
    return ExecuteFilesOnyByOne(argc, argv);
}
