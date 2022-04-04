## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
# install.packages("viridis")
library(viridis)

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

ggplot(data, aes(x=interaction, y=covered_difference, fill=technology)) +
    geom_bar(stat = "identity") + 
  scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Mean Modeled Change in Population Coverage Against the Historical Baseline",
       subtitle = "Reported by Forecast Year, Climate Scenario and Flood Return Period", 
       x = NULL, y = "Change in Population Coverage against the\nHistorical Baseline (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d() +
  # scale_x_discrete(expand = c(0, 0.15)) +
  # scale_y_continuous(expand = c(0, 0), limits=c(0,300)) +
    facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)

path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_difference.png')
ggsave(path, units="in", width=8, height=5, dpi=300)

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

ggplot(data, aes(x=interaction, y=cost_difference, fill=technology)) +
  geom_bar(stat = "identity") + 
  scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Mean Modeled Change in Population Coverage Against the Historical Baseline",
       subtitle = "Reported by Forecast Year, Climate Scenario and Flood Return Period", 
       x = NULL, y = "Change in Population Coverage against the\nHistorical Baseline (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d() +
  facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)

path = file.path(folder, 'figures', 'GHA', 'GHA_covered_pop.png')
ggsave(path, units="in", width=8, height=5, dpi=300)


# # ####################ECONOMIC 
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder, 'figures', 'site_data.csv'))
# 
# data$year = factor(data$year,
#                        levels=c("2030","2050","2080"),
#                        labels=c("2030","2050","2080")
#                    )
# 
# data$returnperiod = factor(data$returnperiod,
#                    # levels=c("rp00100","rp00250",
#                    #          "rp00500","rp01000"),
#                    levels=c("100-year","250-year",
#                             "500-year","1000-year"),
#                    labels=c("100-year","250-year",
#                             "500-year","1000-year")
# )
# # unique(data$climatescenario)
# data$climatescenario = factor(data$climatescenario,
#                    levels=c("rcp4p5","rcp8p5"),
#                    labels=c("RCP 4.5, SSP 2", "RCP 8.5, SSP 3")
# )
# 
# data$cost = (data$cost/1e6)
# 
# ggplot(data, aes(x=year, y=cost, group=climatescenario)) +
#   geom_line(aes(linetype=climatescenario, color=climatescenario))+
#   geom_point(aes(shape=climatescenario, color=climatescenario))+
#   scale_color_manual(values=c("#0072B2", "#D55E00")) +
#   theme( legend.position = "bottom",
#          # axis.text.x = element_text(angle = 0, hjust = 0)
#          ) +
#   labs(colour=NULL,
#        title = "Mobile Infrastructure Damage by Forecast Year, Climate Scenario and Flood Return Period",
#        subtitle = "Riverine Model: MIROC-ESM-CHEM. Coastal Model: RISES-AM",
#        x = NULL, y = "Damage Cost to Mobile Infrastructure ($Mn)") +
#   theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
#   guides(linetype=guide_legend(ncol=2, title='Scenario'),
#          shape=guide_legend(ncol=2, title='Scenario'),
#          color=guide_legend(ncol=2, title='Scenario')) +
#   scale_x_discrete(expand = c(0, 0.15)) +
#   scale_y_continuous(expand = c(0, 0), limits=c(0,300)) +
#   facet_wrap(vars(returnperiod), scales = "free")
# 
# path = file.path(folder, 'figures', 'GHA', 'GHA_economic_cost.png')
# ggsave(path, units="in", width=8, height=6, dpi=300)





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

ggplot(data, aes(x=factor(decile), y=population, fill=covered)) +
  geom_bar(stat="identity", position=position_dodge()) +
  geom_text(aes(ymax=0, x=decile, y=value2 + 1, label=value2), #, color="#FF0000FF"
            size = 2, data = totals, vjust=1, #hjust=1 ,
            position=position_dodge(width = 1)
            ) +
  theme(legend.position = "bottom") +
  labs(colour=NULL,
       title = "Population Coverage by Population Density Decile and Technology",
       subtitle = "Coverage is defined as an Signal-to-Interference-plus-Noise-Ratio (SINR) over zero",
       x = 'Population Density Decile\n(0-10% contains the most populated 10% of 1 km^2 tiles)',
       y = "Population Covered (Millions)",
       fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines"),
        axis.text.x = element_text(angle = 15, hjust=1)) +
  expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, 17.5)) +
  scale_fill_viridis_d() +
  facet_wrap(~technology)

path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_by_deciles.png')
ggsave(path, units="in", width=8, height=6, dpi=300)




