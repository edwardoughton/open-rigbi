## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
# install.packages("viridis")
library(viridis)


# ####################ECONOMIC
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data <- read.csv(file.path(folder, '..','results', 'sites_affected_by_failures_GHA.csv'))

data = data[data$climatescenario == 'rcp4p5' | data$climatescenario == "rcp8p5",]

data = select(data, floodtype, subsidence, year, returnperiod, climatescenario, technology, cost)

data  = data %>% 
  group_by(floodtype, subsidence, year, returnperiod, climatescenario, technology) %>% 
  summarise(cost = sum(cost))

wtsub = data[data$subsidence == "wtsub",] #remove inuncoast
wtsub$subsidence = NULL
model_mean = data[data$subsidence != "wtsub",] 

model_mean  = model_mean %>% 
  group_by(floodtype, climatescenario, year, returnperiod, technology) %>% 
  summarise(cost = mean(cost)) 

data = rbind(wtsub, model_mean) #historical

data$interaction = paste(data$year, data$climatescenario)

data$floodtype = factor(data$floodtype,
                        levels=c("inuncoast","inunriver"),
                        labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c("2030 rcp4p5",
                                   "2050 rcp4p5",
                                   "2080 rcp4p5",
                                   "2030 rcp8p5",
                                   "2050 rcp8p5",
                                   "2080 rcp8p5"),
                          labels=c("2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c("100-year","250-year",
                                    "500-year","1000-year"),
                           labels=c("100-year","250-year",
                                    "500-year","1000-year")
)

data$technology = factor(data$technology,
                         levels=c("GSM","UMTS",
                                  "LTE","NR"),
                         labels=c("2G GSM","3G UMTS",
                                  "4G LTE","5G NR")
)

data$cost = (data$cost/1e6)

totals <- data %>%
  group_by(floodtype, interaction, returnperiod) %>%
  summarize(value = round(sum(cost), 1))

ggplot(data, aes(x=interaction, y=cost)) +
  geom_bar(stat = "identity", aes(fill=technology)) + 
  scale_color_manual(values=c("#0072B2", "#D55E00")) +
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-.5, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
       x = NULL, y = "Economic Damage ($US Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d() +
  # scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,38)) +
  facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)

path = file.path(folder, 'figures', 'GHA', 'GHA_overall_economic_cost_by_event.png')
ggsave(path, units="in", width=8, height=5.5, dpi=300)


# ####################SUPPLY-DEMAND METRICS
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data <- read.csv(file.path(folder, '..', 'results', 'coverage_final_GHA.csv'))

data$interaction = paste(data$year, data$climatescenario)

data$floodtype = factor(data$floodtype,
                         levels=c("inuncoast","inunriver"),
                         labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                              levels=c("2030 rcp4p5",
                                       "2050 rcp4p5",
                                       "2080 rcp4p5",
                                       "2030 rcp8p5",
                                       "2050 rcp8p5",
                                       "2080 rcp8p5"),
                              labels=c("2030 RCP4.5",
                                       "2030 RCP8.5",
                                       "2050 RCP4.5",
                                       "2050 RCP8.5",
                                       "2080 RCP4.5",
                                       "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c("100-year","250-year",
                                    "500-year","1000-year"),
                           labels=c("100-year","250-year",
                                    "500-year","1000-year")
)

data$technology = factor(data$technology,
                           levels=c("GSM","UMTS",
                                    "LTE","NR"),
                           labels=c("2G GSM","3G UMTS",
                                    "4G LTE","5G NR")
)

data$covered_difference = data$covered_difference / 1e6

data = data[data$subsidence == "model_mean" |  data$subsidence == "wtsub",]

totals <- data %>%
  group_by(floodtype, interaction, returnperiod) %>%
  summarize(value = round(sum(covered_difference), 2))

ggplot(data, aes(x=interaction, y=covered_difference)) +
    geom_bar(stat = "identity", aes(fill=technology)) + 
  scale_color_manual(values=c("#0072B2", "#D55E00")) +
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-.5, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme(legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8)) +
  labs(colour=NULL,
       title = "Mean Modeled Change in Population Coverage Against Historic Baseline",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
       x = NULL, y = "Change in Population Coverage against the\nHistorical Baseline (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d() +
  # scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0.1, 0.1)) + #, limits=c(0,2)
    facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)

path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_difference.png')
ggsave(path, units="in", width=8, height=5.5, dpi=300)

########################################################################


# ####################SUPPLY-DEMAND METRICS
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data <- read.csv(file.path(folder, '..', 'results', 'econ_final_GHA.csv'))

data$interaction = paste(data$year, data$climatescenario)

data$floodtype = factor(data$floodtype,
                        levels=c("inuncoast","inunriver"),
                        labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c("2030 rcp4p5",
                                   "2050 rcp4p5",
                                   "2080 rcp4p5",
                                   "2030 rcp8p5",
                                   "2050 rcp8p5",
                                   "2080 rcp8p5"),
                          labels=c("2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c("100-year","250-year",
                                    "500-year","1000-year"),
                           labels=c("100-year","250-year",
                                    "500-year","1000-year")
)

data$technology = factor(data$technology,
                         levels=c("GSM","UMTS",
                                  "LTE","NR"),
                         labels=c("2G GSM","3G UMTS",
                                  "4G LTE","5G NR")
)

data$cost_difference = data$cost_difference / 1e6

data = data[data$subsidence == "model_mean" |  data$subsidence == "wtsub",]

totals <- data %>%
  group_by(floodtype, interaction, returnperiod) %>%
  summarize(value = round(sum(cost_difference), 1))

ggplot(data, aes(x=interaction, y=cost_difference)) +
  geom_bar(stat = "identity", aes(fill=technology)) + 
  scale_color_manual(values=c("#0072B2", "#D55E00")) +
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-.5, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Mean Modeled Change in Estimated Economic Damage Against Historic Baseline",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
       x = NULL, y = "Change in Flooding Damage Costs against the\nHistorical Baseline (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d() +
  scale_y_continuous(expand = c(0.1, 0.1)) + #, limits=c(0,2)
  facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)

path = file.path(folder, 'figures', 'GHA', 'GHA_econ_cost_against_baseline.png')
ggsave(path, units="in", width=8, height=5.5, dpi=300)

# ####################COVERAGE BY DECILES
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data <- read.csv(file.path(folder,'..','data','processed','GHA', 'coverage_by_decile.csv'))

# data$population[data$technology == "NR" | data$decile == 10 | data$covered == 0] <- 0

data$covered = factor(data$covered,
                   levels=c(1,0),
                   labels=c("Covered","Uncovered")
)

data$technology = factor(data$technology,
                      levels=c('GSM', 'UMTS', 'LTE', 'NR'),
                      labels=c("2G GSM","3G UMTS", "4G LTE", "5G NR")
)

data$decile = factor(data$decile,
                         levels=c(10,20,30,40,50,60,70,80,90,100),
                         labels=c('0 -\n10%','10 -\n20%','20 -\n30%','30 -\n40%',
                                  '40 -\n50%','50 -\n60%',
                                  '60 -\n70%','70 -\n80%','80 -\n90%','90 -\n100%'))

data$population = data$population / 1e6

totals <- data %>%
  group_by(decile, covered, technology) %>%
  summarize(value2 = round(population, 1))

# totals$value2[totals$technology == "5G NR" | totals$covered == "uncovered" | totals$decile == "0-10"] <- 0

plot1 = ggplot(data, aes(x=factor(decile), y=population, fill=covered)) +
  geom_bar(stat="identity", position=position_dodge()) +
  geom_text(aes(ymax=0, x=decile, y=value2 + 1, label=value2), #, color="#ffffff"
            size = 2.25, data = totals, vjust=1, #hjust=1 ,
            position=position_dodge(width = 1), show.legend = FALSE
            ) +
  theme(legend.position = "bottom") +
  labs(colour=NULL,
       title = "(A) Population Coverage by Population Density Decile and Technology",
       subtitle = "Coverage is defined as a Signal-to-Interference-plus-Noise-Ratio (SINR) >0 dB",
       x = 'Population Density Decile\n(0-10% contains the most populated 10% of 1 km^2 tiles)',
       y = "Population Coverage (Millions)",
       fill=NULL, color=NULL) +
  theme(panel.spacing = unit(0.6, "lines"),
        axis.text.x = element_text(angle = 15, hjust=1)) +
  expand_limits(y=0) +
  guides() +
  scale_y_continuous(expand = c(0, 0), limits = c(0, 17.5)) +
  scale_fill_viridis_d(direction=1) +
  facet_wrap(~technology)

# path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_by_deciles.png')
# ggsave(path, units="in", width=8, height=6, dpi=300)

# ####################COVERAGE BY DECILES
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data <- read.csv(file.path(folder,'..','data','processed','GHA', 'coverage_by_decile.csv'))

# data$population[data$technology == "NR" | data$decile == 10 | data$covered == 0] <- 0

data$covered = factor(data$covered,
                      levels=c(0, 1),
                      labels=c("Uncovered", "Covered")
)

data$technology = factor(data$technology,
                         levels=c('GSM', 'UMTS', 'LTE', 'NR'),
                         labels=c("2G GSM","3G UMTS", "4G LTE", "5G NR")
)

data$decile = factor(data$decile,
                     levels=c(10,20,30,40,50,60,70,80,90,100),
                     labels=c('0 -\n10%','10 -\n20%','20 -\n30%','30 -\n40%',
                              '40 -\n50%','50 -\n60%',
                              '60 -\n70%','70 -\n80%','80 -\n90%','90 -\n100%'))

data = data %>%
  group_by(technology,decile) %>%
  mutate(countT= sum(population)) %>%
  group_by(covered) %>%
  mutate(perc=round(100*population/countT))

plot2 = ggplot(data, aes(x=factor(decile), y=perc, fill=covered)) +
  geom_bar(stat="identity") +
  geom_text(aes(x=decile, y=perc, label = paste0(perc,"%")),#, color="#ffffff"
            size = 2.25, data = data, vjust=-.75, hjust=.5, 
            show.legend = FALSE, position = position_stack(),
  ) +
  theme(legend.position = "bottom") +
  labs(colour=NULL,
       title = "(B) Percentage Population Coverage by Population Density Decile and Technology",
       subtitle = "Coverage is defined as a Signal-to-Interference-plus-Noise-Ratio (SINR) >0 dB",
       x = 'Population Density Decile\n(0-10% contains the most populated 10% of 1 km^2 tiles)',
       y = "Population Coverage (%)",
       fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines"),
        axis.text.x = element_text(angle = 15, hjust=1)) +
  expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, 100)) +
  scale_fill_viridis_d(direction=-1) +
  facet_wrap(~technology)

############
ggarrange(
  plot1,
  plot2,
  # labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'GHA', 'GHA_panel_plot.png')
ggsave(path, units="in", width=8, height=10, dpi=300)







