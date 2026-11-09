#ifdef FRCOV
#define FIXREVERTER_SIZE 4212
short FIXREVERTER[FIXREVERTER_SIZE];
#include <stdlib.h>
#include <string.h>
__attribute__((constructor(101))) static void fixReverterInitFlags(void) {
  const char *p = getenv("FIXREVERTER"); char *end; long k; int on = 0, i;
  if (p) { while (*p == ' ') p++;
    if (!strncmp(p, "on", 2) && (p[2] == ' ' || !p[2])) { on = 1; p += 2; }
    else if (!strncmp(p, "off", 3) && (p[3] == ' ' || !p[3])) p += 3;
    else if (*p) return; }
  for (i = 0; i < FIXREVERTER_SIZE; i++) FIXREVERTER[i] = (short)!on;
  while (p && *p) { k = strtol(p, &end, 10); if (end == p) { p++; continue; }
    if (k >= 0 && k < FIXREVERTER_SIZE) FIXREVERTER[k] = (short)on; p = end; }
}
#endif
// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <cassert>
#include <cstddef>
#include <cstdint>

#include <functional>
#include <limits>
#include <string>

#include "libxml/parser.h"
#include "libxml/xmlsave.h"

void ignore (void* ctx, const char* msg, ...) {
  // Error handler to avoid spam of error messages from libxml parser.
}


#ifdef FRCOV
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#endif
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
  
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
  xmlSetGenericErrorFunc(NULL, &ignore);

  // Test default empty options value and some random combination.
  std::string data_string(reinterpret_cast<const char*>(data), size);
  const std::size_t data_hash = std::hash<std::string>()(data_string);
  const int max_option_value = std::numeric_limits<int>::max();
  int random_option_value = data_hash % max_option_value;

  // Disable XML_PARSE_HUGE to avoid stack overflow.
  random_option_value &= ~XML_PARSE_HUGE;
  const int options[] = {0, random_option_value};

  for (const auto option_value : options) {
    // Intentionally pass raw data as the API does not require trailing \0.
    if (auto doc = xmlReadMemory(reinterpret_cast<const char*>(data), size,
                                 "noname.xml", NULL, option_value)) {
      auto buf = xmlBufferCreate();
      assert(buf);
      auto ctxt = xmlSaveToBuffer(buf, NULL, 0);
      xmlSaveDoc(ctxt, doc);
      xmlSaveClose(ctxt);
      xmlFreeDoc(doc);
      xmlBufferFree(buf);
    }
  }

  return 0;
}
