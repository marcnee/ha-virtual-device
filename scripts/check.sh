#!/bin/sh
# Runs every check (lint, test, hassfest, test-latest, test-beta) and prints a summary.
# Usage: scripts/check.sh [check ...]   (no argument = all checks)
# A failing check does not stop the others. The beta is informational: it never fails the run.

ALL="lint test hassfest test-latest test-beta"
INFORMATIONAL="test-beta"

checks="${*:-$ALL}"

for check in $checks; do
    case " $ALL " in
        *" $check "*) ;;
        *)
            echo "Unknown check: $check (available: $ALL)" >&2
            exit 2
            ;;
    esac
done

summary=""
status=0
for check in $checks; do
    echo "==> $check"
    if docker compose run --rm "$check"; then
        result="ok"
    else
        case " $INFORMATIONAL " in
            *" $check "*) result="FAILED (informational)" ;;
            *)
                result="FAILED"
                status=1
                ;;
        esac
    fi
    summary="$summary$(printf '%-15s %s' "$check" "$result")
"
done

echo
echo "Summary"
printf '%s' "$summary"
exit "$status"
