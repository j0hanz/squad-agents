from typing import Dict, List


def find_cycles(adjacency_list: Dict[str, List[str]]) -> List[List[str]]:
    """
    Find cycles in a directed graph using an iterative version of Tarjan's
    strongly connected components algorithm. Iterative to avoid Python's
    recursion limit on large/deep import graphs.
    """
    next_index = 0
    index: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    on_stack: Dict[str, bool] = {}
    stack: List[str] = []
    cycles: List[List[str]] = []

    for start in adjacency_list:
        if start in index:
            continue

        index[start] = lowlink[start] = next_index
        next_index += 1
        stack.append(start)
        on_stack[start] = True
        work = [(start, iter(adjacency_list.get(start, [])))]

        while work:
            v, edges = work[-1]
            descended = False
            for w in edges:
                if w not in index:
                    index[w] = lowlink[w] = next_index
                    next_index += 1
                    stack.append(w)
                    on_stack[w] = True
                    work.append((w, iter(adjacency_list.get(w, []))))
                    descended = True
                    break
                elif on_stack.get(w):
                    lowlink[v] = min(lowlink[v], index[w])

            if descended:
                continue

            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[v])

            if lowlink[v] == index[v]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == v:
                        break

                if len(component) > 1:
                    cycles.append(component)
                elif component[0] in adjacency_list.get(component[0], []):
                    cycles.append(component)

    return cycles
