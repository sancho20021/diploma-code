use crate::models::ExecutionResult;

#[derive(Debug)]
pub struct ExecutionMetric {
    pub min_iters: usize,
    pub max_iters: usize,
    pub sum_iters: usize,
}

impl From<ExecutionResult> for ExecutionMetric {
    fn from(result: ExecutionResult) -> Self {
        let iterations: Vec<usize> = result.iterations_per_graph.values().map(|x| *x).collect();
        let min_iters = *iterations.iter().min().unwrap_or(&0);
        let max_iters = *iterations.iter().max().unwrap_or(&0);
        let sum_iters = iterations.iter().sum::<usize>();
        ExecutionMetric {
            min_iters,
            max_iters,
            sum_iters,
        }
    }
}
