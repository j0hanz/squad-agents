export function findCycles(adjacencyList) {
  let index = 0;
  const stack = [];
  const nodes = {};
  const cycles = [];

  function strongconnect(v) {
    nodes[v] = { index, lowlink: index, onStack: true };
    index++;
    stack.push(v);

    const edges = adjacencyList[v] || [];
    for (const w of edges) {
      if (!nodes[w]) {
        strongconnect(w);
        nodes[v].lowlink = Math.min(nodes[v].lowlink, nodes[w].lowlink);
      } else if (nodes[w].onStack) {
        nodes[v].lowlink = Math.min(nodes[v].lowlink, nodes[w].index);
      }
    }

    if (nodes[v].lowlink === nodes[v].index) {
      const component = [];
      let w;
      do {
        w = stack.pop();
        nodes[w].onStack = false;
        component.push(w);
      } while (w !== v);
      
      if (component.length > 1) {
          cycles.push(component);
      }
    }
  }

  for (const v in adjacencyList) {
    if (!nodes[v]) {
      strongconnect(v);
    }
  }

  return cycles;
}
