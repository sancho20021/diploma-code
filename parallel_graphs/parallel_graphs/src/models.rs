use std::collections::{BinaryHeap, HashMap, HashSet};

#[derive(Debug, PartialEq, Eq)]
pub struct Graph {
    pub depth: usize,
    pub width: usize,
}

pub fn graph_batch(n: usize, depth: usize, width: usize) -> Vec<Graph> {
    (0..n).map(|_| Graph { depth, width }).collect()
}

#[derive(Debug, PartialEq, Eq)]
pub struct GraphInstance {
    pub id: usize,
    pub graph: Graph,
    pub left_on_first_layer: Option<usize>,
    pub left_layers: usize,
}

impl GraphInstance {
    pub fn new(id: usize, graph: Graph) -> Self {
        assert!(graph.depth > 0);
        assert!(graph.width > 0);
        let left_on_first_layer = Some(graph.width);
        let left_layers = graph.depth - 1;
        GraphInstance {
            id,
            graph,
            left_on_first_layer,
            left_layers,
        }
    }

    pub fn left_cubes(&self) -> usize {
        self.left_layers * self.graph.width + self.left_on_first_layer.unwrap_or(0)
    }

    /// removes n operations from first layer.
    /// Replaces last layer with previous if it became empty,
    /// in which case returns true.
    pub fn remove_from_first(&mut self, n: usize) -> bool {
        let left_on_first = (&mut self.left_on_first_layer).as_mut().unwrap();
        assert!(n <= *left_on_first);
        *left_on_first -= n;
        if *left_on_first == 0 {
            if self.left_layers == 0 {
                self.left_on_first_layer = None;
            } else {
                self.left_layers -= 1;
                self.left_on_first_layer = Some(self.graph.width);
            }
            return true;
        }
        false
    }
}

impl PartialOrd for GraphInstance {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        match self.left_cubes().partial_cmp(&other.left_cubes()) {
            Some(core::cmp::Ordering::Equal) => {}
            ord => return ord,
        }
        Some(other.id.cmp(&self.id))
    }
}

impl Ord for GraphInstance {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.partial_cmp(other).unwrap()
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct ExecutionResult {
    pub iterations_per_graph: HashMap<usize, usize>,
}

impl ExecutionResult {
    pub fn new() -> Self {
        ExecutionResult {
            iterations_per_graph: HashMap::default(),
        }
    }
}

pub trait Execution
where
    Self: Sized,
{
    /// initializes execution of graphs batch
    fn new(bandwidth: usize, graphs: Vec<Graph>) -> Self;

    /// returns if execution is finished
    fn finished(&self) -> bool;

    /// iterates execution and returns ids of iterated instances
    fn iterate(&mut self) -> Vec<usize>;

    /// executes all graphs
    fn execute(mut self) -> ExecutionResult {
        let mut result = ExecutionResult::new();
        let mut total_iters = 0;
        while !self.finished() {
            let touched_ids = self.iterate();
            total_iters += 1;
            for id in touched_ids {
                result.iterations_per_graph.insert(id, total_iters);
            }
        }
        result
    }
}

pub struct ParallelExecution {
    pub bandwidth: usize,
    pub left_instances: BinaryHeap<GraphInstance>,
}

impl Execution for ParallelExecution {
    fn new(bandwidth: usize, graphs: Vec<Graph>) -> Self {
        ParallelExecution {
            bandwidth,
            left_instances: graphs
                .into_iter()
                .enumerate()
                .map(|(i, graph)| GraphInstance::new(i, graph))
                .collect(),
        }
    }

    fn finished(&self) -> bool {
        self.left_instances.is_empty()
    }

    fn iterate(&mut self) -> Vec<usize> {
        let mut iterated_instances = vec![];
        let mut operations_to_execute = self.bandwidth;
        while operations_to_execute > 0 && !self.finished() {
            let mut first = self.left_instances.pop().unwrap();
            let second = self.left_instances.peek();

            let sub = match second {
                Some(second) => std::cmp::max(
                    [
                        operations_to_execute,
                        first.left_on_first_layer.unwrap(),
                        first.left_cubes() - second.left_cubes(),
                    ]
                    .into_iter()
                    .min()
                    .unwrap(),
                    1,
                ),
                None => std::cmp::min(operations_to_execute, first.left_on_first_layer.unwrap()),
            };
            assert!(sub > 0);

            let before_removal = first.left_cubes();
            first.remove_from_first(sub);
            assert!(first.left_cubes() < before_removal);

            iterated_instances.push(first);
            operations_to_execute -= sub;
        }
        let touched_instances = iterated_instances.iter().map(|inst| inst.id).collect();
        for instance in iterated_instances {
            if instance.left_cubes() > 0 {
                self.left_instances.push(instance);
            }
        }
        touched_instances
    }
}

pub struct SequentialExecution {
    pub bandwidth: usize,
    pub left_instances: Vec<GraphInstance>,
}

impl Execution for SequentialExecution {
    fn new(bandwidth: usize, graphs: Vec<Graph>) -> Self {
        SequentialExecution {
            bandwidth,
            left_instances: graphs
                .into_iter()
                .enumerate()
                .map(|(i, graph)| GraphInstance::new(i, graph))
                .collect(),
        }
    }

    fn finished(&self) -> bool {
        self.left_instances.is_empty()
    }

    fn iterate(&mut self) -> Vec<usize> {
        let mut touched_instances = HashSet::new();
        let mut bandwidth_left = self.bandwidth;

        for instance in self.left_instances.iter_mut().rev() {
            if bandwidth_left == 0 {
                break;
            }
            let sub = std::cmp::min(bandwidth_left, instance.left_on_first_layer.unwrap());
            assert!(sub > 0);
            instance.remove_from_first(sub);
            touched_instances.insert(instance.id);
            bandwidth_left -= sub;
        }
        while let Some(instance) = self.left_instances.last() {
            if instance.left_cubes() == 0 {
                self.left_instances.pop().unwrap();
            } else {
                break;
            }
        }
        touched_instances.into_iter().collect()
    }
}

pub struct Given {
    graphs: usize,
    depth: usize,
    width: usize,
    bandwidth: usize,
}

pub fn given(graphs: usize, depth: usize, width: usize, bandwidth: usize) -> Given {
    Given {
        graphs,
        depth,
        width,
        bandwidth,
    }
}

impl Given {
    pub fn expect<E: Execution>(&self, iterations_per_graph: &[(usize, usize)]) {
        let result = self.execute::<E>();

        let iterations_per_graph: HashMap<usize, usize> = iterations_per_graph
            .into_iter()
            .map(|(a, b)| (*a, *b))
            .collect();

        assert_eq!(
            result,
            ExecutionResult {
                iterations_per_graph,
            }
        );
    }

    pub fn execute<E: Execution>(&self) -> ExecutionResult {
        let graphs = graph_batch(self.graphs, self.depth, self.width);
        let execution = E::new(self.bandwidth, graphs);
        execution.execute()
    }
}

#[cfg(test)]
pub mod tests {

    const ONE: usize = 1;
    const TWO: usize = 2;

    mod parallel_execution_test {
        use crate::models::{
            given,
            tests::{ONE, TWO},
            ParallelExecution,
        };

        #[test]
        fn test_no_graphs() {
            given(0, 1, 1, ONE).expect::<ParallelExecution>(&[]);
        }

        #[test]
        fn test_one_graph() {
            given(1, 1, 1, ONE).expect::<ParallelExecution>(&[(0, 1)]);
        }

        #[test]
        fn test_depth() {
            given(1, 10, 1, ONE).expect::<ParallelExecution>(&[(0, 10)]);
        }

        #[test]
        fn test_bamboo_double_bandwidth() {
            given(1, 10, 1, TWO).expect::<ParallelExecution>(&[(0, 10)]);
        }

        #[test]
        fn test_width() {
            given(1, 1, 2, TWO).expect::<ParallelExecution>(&[(0, 1)]);
        }

        #[test]
        fn test_batch() {
            given(2, 1, 1, TWO).expect::<ParallelExecution>(&[(0, 1), (1, 1)]);
        }

        #[test]
        fn test_non_trivial_bamboo() {
            given(3, 2, 1, TWO).expect::<ParallelExecution>(&[(0, 2), (1, 3), (2, 3)]);
        }

        #[test]
        fn test_non_trivial_parallel_graphs() {
            given(3, 1, 2, TWO).expect::<ParallelExecution>(&[(0, 2), (1, 3), (2, 3)]);
        }
    }

    mod sequential_execution_test {
        use crate::models::{given, SequentialExecution};

        use super::{ONE, TWO};

        #[test]
        fn test_no_graphs() {
            given(0, 1, 1, ONE).expect::<SequentialExecution>(&[]);
        }

        #[test]
        fn test_one_graph() {
            given(1, 1, 1, ONE).expect::<SequentialExecution>(&[(0, 1)]);
        }

        #[test]
        fn test_depth() {
            given(1, 10, 1, ONE).expect::<SequentialExecution>(&[(0, 10)]);
        }

        #[test]
        fn test_bamboo_double_bandwidth() {
            given(1, 10, 1, TWO).expect::<SequentialExecution>(&[(0, 10)]);
        }

        #[test]
        fn test_width() {
            given(1, 1, 2, TWO).expect::<SequentialExecution>(&[(0, 1)]);
        }

        #[test]
        fn test_batch1() {
            given(2, 1, 1, TWO).expect::<SequentialExecution>(&[(0, 1), (1, 1)]);
        }

        #[test]
        fn test_batch2() {
            given(2, 1, 1, ONE).expect::<SequentialExecution>(&[(0, 2), (1, 1)]);
        }

        #[test]
        fn test_non_trivial_bamboo() {
            given(3, 2, 1, TWO).expect::<SequentialExecution>(&[(0, 4), (1, 2), (2, 2)]);
        }

        #[test]
        fn test_non_trivial_parallel_graphs() {
            given(3, 1, 2, TWO).expect::<SequentialExecution>(&[(0, 3), (1, 2), (2, 1)]);
        }
    }
}
