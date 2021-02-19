library(tidyverse)

raw_data <- read_csv("data.csv")
all_data <- raw_data %>% 
  mutate(name = paste(infra, initial_divides, online_divides))

cactus_data <- all_data %>%
  filter(jobs == 64) %>%
  filter(result != "TIMEOUT")
ggplot(data = cactus_data) +
  geom_histogram(mapping = aes(x = name), stat="count") +
  theme(axis.text.x=element_text(angle=45,hjust=1))
ggsave("solved-hist.pdf")
ggplot(data = cactus_data %>%
         filter(name %in% c("gg-local 6 2", "cnc-lingeling 8 2", "parac 4 4")) %>%
         group_by(name) %>%
         arrange(duration) %>%
         mutate(ct = row_number())
         ) +
  geom_step(aes(y=duration, x = ct, color = name)) +
  labs(y= "Seconds", x = "Solved", color = "System") +
  annotate("segment", x = 0, y = 3600, xend = 15, yend = 3600) +
  xlim(0, 15)
ggsave("cactus.pdf")
scale_sys_data <- raw_data %>%
         filter((infra == "gg-local" & online_divides == 2 & 2 ** initial_divides == jobs) | (infra == "cnc-lingeling" & online_divides == 2) | (infra == "parac" & online_divides == 4)) %>%
         filter(result != "TIMEOUT") %>%
         filter(family == "cnc")
print(scale_sys_data)
ggplot( scale_sys_data %>%
         group_by(infra,jobs) %>%
         summarise(solved = n())
     ) +
  geom_point(mapping = aes(x = jobs, y = solved, color = infra)) +
  geom_line(mapping = aes(x = jobs, y = solved, color = infra)) +
  labs(x = "Parallelism", y = "Solved", color = "System")
ggsave("scale.pdf")
