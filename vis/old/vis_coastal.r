## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
# install.packages("viridis")
# library(viridis)
install.packages("llply")
require(llply)
library(stringr)

###################
#####Aggregate cells by income
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results_v2')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inuncoast")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       cell_count_high=numeric(),
                       cost_usd_low=numeric(),
                       cost_usd_baseline=numeric(),
                       cost_usd_high=numeric()
) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$�..country = NULL
data = merge(data, lut, by=c("iso3","iso3"))

rm(empty_df, import_function, lut)

data = data %>%
  separate(file, 
           into = c(
             "hazard_type", 
             "climatescenario", 
             "subsidence_model", 
             "year", 
             "returnperiod",
             "zero",
             "perc",
             "percentile"), 
           sep = "_",
           convert = TRUE)

data = data[
  data$climatescenario == 'historical' | 
    data$climatescenario == 'rcp4p5' | 
    data$climatescenario == "rcp8p5",]

data$climatescenario = factor(data$climatescenario,
                              levels=c("historical","rcp4p5","rcp8p5"),
                              labels=c("Historical","RCP4.5","RCP8.5")
)

data$returnperiod =  gsub(".csv", "", data$returnperiod) 

#replace return periods
data$returnperiod =  gsub("rp00002", "rp0002", data$returnperiod)
data$returnperiod =  gsub("rp00005", "rp0005", data$returnperiod)
data$returnperiod =  gsub("rp00010", "rp0010", data$returnperiod)
data$returnperiod =  gsub("rp00025", "rp0025", data$returnperiod)
data$returnperiod =  gsub("rp00050", "rp0050", data$returnperiod)
data$returnperiod =  gsub("rp00100", "rp0100", data$returnperiod)
data$returnperiod =  gsub("rp00250", "rp0250", data$returnperiod)
data$returnperiod =  gsub("rp00500", "rp0500", data$returnperiod)
data$returnperiod =  gsub("rp01000", "rp1000", data$returnperiod)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$returnperiod == "rp0002"] = "50%" # (1/2) * 100 = 50%
data$probability[data$returnperiod == "rp0005"] = "20%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0010"] = "10%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0025"] = "4%" # (1/25) * 100 = 4%
data$probability[data$returnperiod == "rp0050"] = "2%" # (1/50) * 100 = 2%
data$probability[data$returnperiod == "rp0100"] = "1%" # (1/100) * 100 = 1%
data$probability[data$returnperiod == "rp0250"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$returnperiod == "rp0500"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$returnperiod == "rp1000"] = "0.1%" # (1/1000) * 100 = .1%

data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%",
                            "2%",
                            "4%",
                            "10%",
                            "20%",
                            "50%"
                          )
)

data = data[data$probability == "0.1%"  |
              data$probability == "0.2%"  |
              data$probability == "0.4%"  |
              data$probability == "1%", ] 

data$radio = factor(data$radio,
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$interaction = paste(data$climatescenario, data$year)

data$interaction = factor(data$interaction,
                                     levels=c(
                                       "Historical hist",
                                       "Historical 2030",
                                       "Historical 2050",
                                       "Historical 2080",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

data$income_group = factor(data$income_group,
                    levels=c("LIC","LMC",
                             "UMC","HIC")
)

data = data[data$subsidence_model != 'nosub', ] 
data$subsidence_model = NULL

data = data %>%
  mutate_at(vars(percentile), ~replace_na(., "high"))

data$percentile = gsub("05.csv", "low", data$percentile)
data$percentile = gsub("50.csv", "mean", data$percentile)
data$percentile[data$climatescenario == 'Historical'] <- 'mean'  

data$zero = NULL
data$perc = NULL
data$network = NULL

data = data[complete.cases(data),] 
# data = data[complete.cases(data$radio),] 

data_aggregated  = data %>%
  group_by(income_group, interaction, probability, #returnperiod,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cell_count)

data_aggregated$interaction = factor(data_aggregated$interaction,
                          levels=c(
                            "Historical 1980",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(income_group, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    income_group = 'LIC', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )

max_y_value = max(df_errorbar$high, na.rm = T)

plot1 = 
  ggplot(data_aggregated, 
        aes(x=interaction, y=mean, fill=income_group)) + 
    geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,2),"Mn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.8, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Mobile Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Income Group.", 
       x = "Annual Probability", y = "Cells (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Income Group')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/3))) +
  facet_wrap(~probability, ncol=4, nrow=1)

data_aggregated  = data %>%
  group_by(income_group, interaction, probability, percentile) %>%
  summarise(cost_usd = round(sum(cost_usd_baseline)/1e9, 4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cost_usd)

data_aggregated$interaction = factor(data_aggregated$interaction,
                                     levels=c(
                                       "Historical 1980",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(income_group, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    income_group = 'LIC', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )
max_y_value = max(df_errorbar$high, na.rm = T)

plot2 = 
  ggplot(data_aggregated, 
         aes(x=interaction, y=mean, fill=income_group)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,1),"Bn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.7, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Damage Costs to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Income Group.", 
       x = "Annual Probability", y = "Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Income Group')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/2.5))) +
  facet_wrap(~probability, ncol=4, nrow=1)

ggarrange(
  plot1, 
  plot2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_coastal_flooding_by_income.png')
ggsave(path, units="in", width=8, height=8, dpi=300)


###################
#####Aggregate cells by generation
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results_v2')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inuncoast")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       cell_count_high=numeric(),
                       cost_usd_low=numeric(),
                       cost_usd_baseline=numeric(),
                       cost_usd_high=numeric()
) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$�..country = NULL
data = merge(data, lut, by=c("iso3","iso3"))

rm(empty_df, import_function, lut)

data = data %>%
  separate(file, 
           into = c(
             "hazard_type", 
             "climatescenario", 
             "subsidence_model", 
             "year", 
             "returnperiod",
             "zero",
             "perc",
             "percentile"), 
           sep = "_",
           convert = TRUE)

data = data[
  data$climatescenario == 'historical' | 
    data$climatescenario == 'rcp4p5' | 
    data$climatescenario == "rcp8p5",]

data$climatescenario = factor(data$climatescenario,
                              levels=c("historical","rcp4p5","rcp8p5"),
                              labels=c("Historical","RCP4.5","RCP8.5")
)

data$returnperiod =  gsub(".csv", "", data$returnperiod) 

#replace return periods
data$returnperiod =  gsub("rp00002", "rp0002", data$returnperiod)
data$returnperiod =  gsub("rp00005", "rp0005", data$returnperiod)
data$returnperiod =  gsub("rp00010", "rp0010", data$returnperiod)
data$returnperiod =  gsub("rp00025", "rp0025", data$returnperiod)
data$returnperiod =  gsub("rp00050", "rp0050", data$returnperiod)
data$returnperiod =  gsub("rp00100", "rp0100", data$returnperiod)
data$returnperiod =  gsub("rp00250", "rp0250", data$returnperiod)
data$returnperiod =  gsub("rp00500", "rp0500", data$returnperiod)
data$returnperiod =  gsub("rp01000", "rp1000", data$returnperiod)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$returnperiod == "rp0002"] = "50%" # (1/2) * 100 = 50%
data$probability[data$returnperiod == "rp0005"] = "20%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0010"] = "10%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0025"] = "4%" # (1/25) * 100 = 4%
data$probability[data$returnperiod == "rp0050"] = "2%" # (1/50) * 100 = 2%
data$probability[data$returnperiod == "rp0100"] = "1%" # (1/100) * 100 = 1%
data$probability[data$returnperiod == "rp0250"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$returnperiod == "rp0500"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$returnperiod == "rp1000"] = "0.1%" # (1/1000) * 100 = .1%

data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%",
                            "2%",
                            "4%",
                            "10%",
                            "20%",
                            "50%"
                          )
)

data = data[data$probability == "0.1%"  |
              data$probability == "0.2%"  |
              data$probability == "0.4%"  |
              data$probability == "1%", ] 


data$radio = factor(data$radio,
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)
data = data[complete.cases(data$radio),] 

data$interaction = paste(data$climatescenario, data$year)

data$interaction = factor(data$interaction,
                          levels=c(
                            "Historical hist",
                            "Historical 2030",
                            "Historical 2050",
                            "Historical 2080",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
)

data = data[data$subsidence_model != 'nosub', ] 
data$subsidence_model = NULL

data = data %>%
  mutate_at(vars(percentile), ~replace_na(., "high"))

data$percentile = gsub("05.csv", "low", data$percentile)
data$percentile = gsub("50.csv", "mean", data$percentile)
data$percentile[data$climatescenario == 'Historical'] <- 'mean'  

data$zero = NULL
data$perc = NULL
data$network = NULL

data = data[complete.cases(data),] 

data_aggregated  = data %>%
  group_by(radio, interaction, probability, #returnperiod,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cell_count)
unique(data_aggregated$interaction)

data_aggregated$interaction = factor(data_aggregated$interaction,
                                     levels=c(
                                       "Historical 1980",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(radio, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    radio = '2G GSM', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )

max_y_value = max(df_errorbar$high, na.rm = T)

plot1 = ggplot(data_aggregated, 
         aes(x=interaction, y=mean, fill=radio)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,2),"Mn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.8, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Mobile Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Cellular Generation.", 
       x = "Annual Probability", y = "Cells (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Generation')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/3))) +
  facet_wrap(~probability, ncol=4, nrow=1)

data_aggregated  = data %>%
  group_by(radio, interaction, probability, percentile) %>%
  summarise(cost_usd = round(sum(cost_usd_baseline)/1e9, 4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cost_usd)

data_aggregated$interaction = factor(data_aggregated$interaction,
                                     levels=c(
                                       "Historical 1980",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(radio, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    radio = '5G NR', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )
max_y_value = max(df_errorbar$high, na.rm = T)

plot2 = 
  ggplot(data_aggregated, 
         aes(x=interaction, y=mean, fill=radio)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,1),"Bn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.7, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Damage Costs to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Cellular Generation.", 
       x = "Annual Probability", y = "Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/2.5))) +
  facet_wrap(~probability, ncol=4, nrow=1)

ggarrange(
  plot1, 
  plot2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_coastal_flooding_by_generation.png')
ggsave(path, units="in", width=8, height=8, dpi=300)




###################
#####Aggregate cells by region
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results_v2')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inuncoast")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       cell_count_high=numeric(),
                       cost_usd_low=numeric(),
                       cost_usd_baseline=numeric(),
                       cost_usd_high=numeric()
) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$�..country = NULL
data = merge(data, lut, by=c("iso3","iso3"))

rm(empty_df, import_function, lut)

data = data %>%
  separate(file, 
           into = c(
             "hazard_type", 
             "climatescenario", 
             "subsidence_model", 
             "year", 
             "returnperiod",
             "zero",
             "perc",
             "percentile"), 
           sep = "_",
           convert = TRUE)

data = data[
  data$climatescenario == 'historical' | 
    data$climatescenario == 'rcp4p5' | 
    data$climatescenario == "rcp8p5",]

data$climatescenario = factor(data$climatescenario,
                              levels=c("historical","rcp4p5","rcp8p5"),
                              labels=c("Historical","RCP4.5","RCP8.5")
)

data$returnperiod =  gsub(".csv", "", data$returnperiod) 

#replace return periods
data$returnperiod =  gsub("rp00002", "rp0002", data$returnperiod)
data$returnperiod =  gsub("rp00005", "rp0005", data$returnperiod)
data$returnperiod =  gsub("rp00010", "rp0010", data$returnperiod)
data$returnperiod =  gsub("rp00025", "rp0025", data$returnperiod)
data$returnperiod =  gsub("rp00050", "rp0050", data$returnperiod)
data$returnperiod =  gsub("rp00100", "rp0100", data$returnperiod)
data$returnperiod =  gsub("rp00250", "rp0250", data$returnperiod)
data$returnperiod =  gsub("rp00500", "rp0500", data$returnperiod)
data$returnperiod =  gsub("rp01000", "rp1000", data$returnperiod)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$returnperiod == "rp0002"] = "50%" # (1/2) * 100 = 50%
data$probability[data$returnperiod == "rp0005"] = "20%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0010"] = "10%" # (1/10) * 100 = 10%
data$probability[data$returnperiod == "rp0025"] = "4%" # (1/25) * 100 = 4%
data$probability[data$returnperiod == "rp0050"] = "2%" # (1/50) * 100 = 2%
data$probability[data$returnperiod == "rp0100"] = "1%" # (1/100) * 100 = 1%
data$probability[data$returnperiod == "rp0250"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$returnperiod == "rp0500"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$returnperiod == "rp1000"] = "0.1%" # (1/1000) * 100 = .1%

data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%",
                            "2%",
                            "4%",
                            "10%",
                            "20%",
                            "50%"
                          )
)

data = data[data$probability == "0.1%"  |
              data$probability == "0.2%"  |
              data$probability == "0.4%"  |
              data$probability == "1%", ] 

data$radio = factor(data$radio,
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$interaction = paste(data$climatescenario, data$year)

data$interaction = factor(data$interaction,
                          levels=c(
                            "Historical hist",
                            "Historical 2030",
                            "Historical 2050",
                            "Historical 2080",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
)


data = data[data$subsidence_model != 'nosub', ] 
data$subsidence_model = NULL

data = data %>%
  mutate_at(vars(percentile), ~replace_na(., "high"))
# unique(data$percentile)
data$percentile = gsub("05.csv", "low", data$percentile)
data$percentile = gsub("50.csv", "mean", data$percentile)
data$percentile[data$climatescenario == 'Historical'] <- 'mean'  

data$zero = NULL
data$perc = NULL
data$network = NULL

data = data[complete.cases(data),] 

data$region = factor(data$region,
                     levels=c(
                       "East Asia & Pacific",
                       "Europe & Central Asia",
                       "Latin America & Caribbean",
                       "Middle East & North Africa",
                       "North America",
                       "South Asia",
                       "Sub-Saharan Africa"
                     ),
)

data = data[complete.cases(data$radio),] 

data_aggregated  = data %>%
  group_by(region, interaction, probability, #returnperiod,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cell_count)

data_aggregated$interaction = factor(data_aggregated$interaction,
                                     levels=c(
                                       "Historical 1980",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(region, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    region = 'Sub-Saharan Africa', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )

max_y_value = max(df_errorbar$high, na.rm = T)

plot1 = ggplot(data_aggregated, 
               aes(x=interaction, y=mean, fill=region)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,2),"Mn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.8, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Mobile Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Region.", 
       x = "Annual Probability", y = "Cells (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=4, title='Region')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/3))) +
  facet_wrap(~probability, ncol=4, nrow=1)

data_aggregated  = data %>%
  group_by(region, interaction, probability, percentile) %>%
  summarise(cost_usd = round(sum(cost_usd_baseline)/1e9, 4))

hist = data_aggregated[data_aggregated$interaction == 'Historical hist', ] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical hist',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2030',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2050',] 
data_aggregated = data_aggregated[data_aggregated$interaction != 'Historical 2080',] 
hist$interaction = "Historical 1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cost_usd)

data_aggregated$interaction = factor(data_aggregated$interaction,
                                     levels=c(
                                       "Historical 1980",
                                       "RCP4.5 2030",
                                       "RCP8.5 2030",
                                       "RCP4.5 2050",
                                       "RCP8.5 2050",
                                       "RCP4.5 2080",
                                       "RCP8.5 2080"),
)

df_errorbar <- 
  data_aggregated |>
  group_by(region, interaction, probability) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    region = 'Sub-Saharan Africa', 
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )
max_y_value = max(df_errorbar$high, na.rm = T)

plot2 = 
  ggplot(data_aggregated, 
         aes(x=interaction, y=mean, fill=region)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  geom_text(data = df_errorbar, aes(label = paste(round(mean,1),"Bn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.7, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Damage Costs to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, Climate Scenario and Region.", 
       x = "Annual Probability", y = "Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=4, title='Region')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/2.5))) +
  facet_wrap(~probability, ncol=4, nrow=1)

ggarrange(
  plot1, 
  plot2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_coastal_flooding_by_region.png')
ggsave(path, units="in", width=8, height=8, dpi=300)
