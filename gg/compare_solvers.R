library(tidyverse)
data <- read_csv("data.csv")
data$solver = paste(data$infra, data$painless_mode, sep = "-")
filtered <- data %>% filter((jobs == 16 | infra == "cadical") & timeout == 3600 & family == "easy" & trial == 0) %>% filter(result != "TIMEOUT")
n_solvers <- length(unique(filtered$solver))
common_benchmarks <- (filtered %>% group_by(benchmark) %>% summarize(count = n()) %>% filter(count == n_solvers))$benchmark
common_times <- filtered %>% filter(benchmark %in% common_benchmarks) %>% group_by(infra, painless_mode) %>% summarise(sum_duration = sum(duration))
aggregated <- filtered %>% group_by(infra, painless_mode) %>% summarise(count = n(), sum_duration = sum(duration))
aggregated
ggplot
common_times
