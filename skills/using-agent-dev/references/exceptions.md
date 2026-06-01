# Exceptions to Phase Discipline

Not all work requires four full phases. Apply judgment:

| Work Type               | Phases Required                             |
| ----------------------- | ------------------------------------------- |
| New feature / component | All four (Design → Build → Validate → Ship) |
| Bug fix (non-trivial)   | Build → Validate → Ship                     |
| Hotfix / one-liner      | Build → Ship (document reason for skipping) |
| Documentation only      | Build → Ship                                |
| Exploratory research    | Design only                                 |

When skipping phases, leave a one-line comment in the commit message explaining why.
