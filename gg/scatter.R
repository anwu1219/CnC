library(tidyverse)
library(gridExtra)

data <- read_csv("data.csv")
data$solver = paste(data$infra, data$painless_mode, sep = "_")
filtered <- data %>% filter((jobs == 8 | infra == "cadical") & timeout == 3600 & ( family == "easy" | family == "cnc" ) & trial == 0) %>% filter(result != "TIMEOUT")
aggregated <- filtered %>% select(benchmark, family, solver, duration) %>% group_by(benchmark)
aggregated<- pivot_wider(aggregated, names_from = solver, values_from = duration)
aggregated[is.na(aggregated)] <- 3600
aggregated

pair <- function(solverA, solverB, hideLegend=FALSE) {
  return(ggplot(aggregated, aes_string(y=sprintf("`%s`", solverA),x=sprintf("`%s`", solverB),shape="family",color="family")) +
           theme_light() +
           geom_point(size = 4, alpha=1.0) +
           scale_y_continuous(limits=c(1,3600)) +
           scale_x_continuous(limits=c(1,3600), trans="log10") +
           labs(
             title = sprintf("%s v. %s", solverA, solverB),
             shape = "Family",
             color = "Family",
             y = sprintf("%s time (s)", solverA),
             x = sprintf("%s time (s)", solverB)
           ) +
           annotate("segment", x = 1, xend = 3600, y = 1, yend = 3600, size=0.1, linetype=2) +
           annotate("segment", x = 2, xend = 3600, y = 1, yend = 1800, size=0.1, linetype=2) +
           annotate("segment", x = 8, xend = 3600, y = 1, yend = 450 , size=0.1, linetype=2) +
           annotate("segment", y = 2, yend = 3600, x = 1, xend = 1800, size=0.1, linetype=2) +
           annotate("segment", y = 8, yend = 3600, x = 1, xend = 450 , size=0.1, linetype=2) +
           annotate("segment", y = 1, yend = 3600, x = 3600, xend = 3600 , size=0.1, linetype=1) +
           annotate("segment", x = 1, xend = 3600, y = 3600, yend = 3600 , size=0.1, linetype=1) +
           annotate("text", y = 3400, x = 1600, label = "2x") +
           annotate("text", y = 3400, x = 390, label = "8x") + 
           theme(plot.margin = margin(0.1, 0.1, 0.3,0.1,  unit = "in"),
                 legend.position = (if (hideLegend) {"none"} else {"right"})))
}

#pair(`cadical-default`, `gg-local-default`)
a = pair("gg_local_default", "cnc_lingeling_default")
b = pair("gg_local_default", "plingeling_default")
c = pair("gg_local_default", "cadical_default")
d = pair("gg_local_default", "painless_default")
e = pair("gg_local_default", "painless_dnc")
p <- arrangeGrob(a, b, c, d, e, nrow = 3, ncol = 2, top = "Pairwise Comparisons of Solvers")
ggsave(p, file="pairwise.pdf", height = 13, width = 10, units = "in")
