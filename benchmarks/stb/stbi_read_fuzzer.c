#ifdef FRCOV
#define FIXREVERTER_SIZE 126
short FIXREVERTER[FIXREVERTER_SIZE];
#endif
#define STB_IMAGE_IMPLEMENTATION
#include "../stb_image.h"


#ifdef FRCOV
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size)
{
    
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
    int x, y, channels;

    if(!stbi_info_from_memory(data, size, &x, &y, &channels)) return 0;

    /* exit if the image is larger than ~80MB */
    if(y && x > (80000000 / 4) / y) return 0;

    unsigned char *img = stbi_load_from_memory(data, size, &x, &y, &channels, 4);

    free(img);

    return 0;
}
