import re


# Parse FixReverter logs into reached (program execution reaches the injection)  injection ids
# and triggered (program execution meets the injected condition(s)) injection ids.
def parse_log(output: str) -> tuple:
    # Deduplicate first: an input stuck in a loop around an injection can print
    # the same line millions of times, and only distinct ids matter.
    lines = set(output.split('\n'))
    reaches = set()
    triggers = set()
    for line in lines:
        reach_match = re.search(r'reached bug index (\d+)', line)
        if reach_match:
            reaches.add(int(reach_match.group(1)))
        else:
            trigger_match = re.search(r'triggered bug index (\d+)', line)
            if trigger_match:
                # Logging of `trigger` suppresses logging of `reach`.
                reaches.add(int(trigger_match.group(1)))
                triggers.add(int(trigger_match.group(1)))
    # Sort and convert to list.
    return sorted(reaches), sorted(triggers)
