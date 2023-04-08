use std::{error::Error, io};

use models::Execution;
use serde::{Deserialize, Serialize};

use crate::{
    models::{given, ParallelExecution, SequentialExecution},
    view::ExecutionMetric,
};

mod models;
mod view;

#[derive(Debug, Serialize, Deserialize)]
pub struct Record {
    graphs_number: usize,
    graph_depth: usize,
    graph_width: usize,
    bandwidth: usize,
    min_iters: usize,
    max_iters: usize,
    sum_iters: usize,
}

pub fn linspace(start: usize, end: usize, n: usize) -> Vec<usize> {
    let dx = (end - start) / (n - 1);
    let mut x = vec![start; n];
    for i in 1..n {
        x[i] = x[i - 1] + dx;
    }
    x
}

pub fn write_dataset<E: Execution>(
    min_graphs: usize,
    max_graphs: usize,
    len: usize,
    file: String,
) -> Result<(), Box<dyn Error>> {
    let graph_depth = 5;
    let graph_width = 5;
    let bandwidth = 5 * 200;

    let mut wtr = csv::Writer::from_path(file)?;

    for graphs_number in linspace(min_graphs, max_graphs, len) {
        let metric: ExecutionMetric = given(graphs_number, graph_depth, graph_width, bandwidth)
            .execute::<E>()
            .into();
        let record = Record {
            graphs_number,
            graph_depth,
            graph_width,
            bandwidth,
            min_iters: metric.min_iters,
            max_iters: metric.max_iters,
            sum_iters: metric.sum_iters,
        };
        wtr.serialize(record)?;
    }
    wtr.flush()?;
    Ok(())
}

fn main() {
    let min_graphs = 10;
    let max_graphs = 5_000;
    let len = 40;

    write_dataset::<ParallelExecution>(min_graphs, max_graphs, len, "parallel.csv".to_string())
        .unwrap();
    write_dataset::<SequentialExecution>(min_graphs, max_graphs, len, "sequential.csv".to_string())
        .unwrap();
}
