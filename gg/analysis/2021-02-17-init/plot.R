library(tidyverse)

d <- read_csv("data.csv") %>% 
  mutate(name = paste(infra, initial_divides, online_divides)) %>%
  filter(jobs == 64) %>%
  filter(result != "TIMEOUT")
ggplot(data = d) +
  geom_histogram(mapping = aes(x = name), stat="count") +
  theme(axis.text.x=element_text(angle=45,hjust=1))
ggsave("solved-hist.pdf")
ggplot(data = d %>%
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
