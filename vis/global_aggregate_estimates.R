## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
library(stringr)

###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inuncoast")

empty_df <- data.frame(iso3=character(),
                       # iso2=character(),
                       # country=character(),
                       # continent=character(),
                       # radio=character(),
                       # network=character(),
                       # cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       # cell_count_high=numeric(),
                       # cost_usd_low=numeric(),
                       cost_usd_baseline=numeric()#,
                       # cost_usd_high=numeric()
)

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

# data = data[(data$radio == 'LTE' | data$radio == 'UMTS'),]
# data = data[(data$radio == 'GSM'),]
# data = data[complete.cases(data[ , c('radio')]), ]

rm(empty_df, import_function)
data$file2 = data$file

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
# data$returnperiod =  gsub("rp00002", "rp0002", data$returnperiod)
# data$returnperiod =  gsub("rp00005", "rp0005", data$returnperiod)
# data$returnperiod =  gsub("rp00010", "rp0010", data$returnperiod)
# data$returnperiod =  gsub("rp00025", "rp0025", data$returnperiod)
# data$returnperiod =  gsub("rp00050", "rp0050", data$returnperiod)
data$returnperiod =  gsub("rp00100", "rp0100", data$returnperiod)
data$returnperiod =  gsub("rp00250", "rp0250", data$returnperiod)
data$returnperiod =  gsub("rp00500", "rp0500", data$returnperiod)
data$returnperiod =  gsub("rp01000", "rp1000", data$returnperiod)

#convert to probability_of_exceedance
data$probability = ''
# data$probability[data$returnperiod == "rp0002"] = "50%" # (1/2) * 100 = 50%
# data$probability[data$returnperiod == "rp0005"] = "20%" # (1/10) * 100 = 10%
# data$probability[data$returnperiod == "rp0010"] = "10%" # (1/10) * 100 = 10%
# data$probability[data$returnperiod == "rp0025"] = "4%" # (1/25) * 100 = 4%
# data$probability[data$returnperiod == "rp0050"] = "2%" # (1/50) * 100 = 2%
data$probability[data$returnperiod == "rp0100"] = "1%" # (1/100) * 100 = 1%
data$probability[data$returnperiod == "rp0250"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$returnperiod == "rp0500"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$returnperiod == "rp1000"] = "0.1%" # (1/1000) * 100 = .1%

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "rp0002",
                             # "rp0005",
                             # "rp0010",
                             # "rp0025",
                             # "rp0050",
                             "rp0100",
                             "rp0250",
                             "rp0500",
                             "rp1000"
                           ),
                           labels=c(
                             # "1-in-2-Years",
                             # "1-in-5-Years",
                             # "1-in-10-Years",
                             # "1-in-25-Years",
                             # "1-in-50-Years",
                             "1-in-100-Years",
                             "1-in-250-Years",
                             "1-in-500-Years",
                             "1-in-1000-Years"
                           )
)

data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%"#,
                            # "2%",
                            # "4%",
                            # "10%",
                            # "20%",
                            # "50%"
                          )
)

data = data[data$probability == "0.1%"  |
              data$probability == "0.2%"  |
              data$probability == "0.4%"  |
              data$probability == "1%", ]

# data$radio = factor(data$radio,
#                     levels=c("GSM","UMTS",
#                              "LTE","NR"),
#                     labels=c("2G GSM","3G UMTS",
#                              "4G LTE","5G NR"
#                     )
# )

data = data[data$subsidence_model != 'nosub', ]
data$subsidence_model = NULL
# write_csv(data, file.path(folder, 'test.csv'))

data = data %>%
  # mutate_at(vars(percentile), ~replace_na(., "high"))
  mutate(percentile = replace_na(as.character(percentile), "high"))
data$percentile = gsub("50", "mean", data$percentile)
data$percentile = gsub("5", "low", data$percentile)
write_csv(data, file.path(folder, 'test.csv'))

data$percentile[data$climatescenario == 'Historical'] <- 'mean'

data$zero = NULL
data$perc = NULL

####
folder = dirname(rstudioapi::getSourceEditorContext()$path)
path_in = file.path(folder, '..', 'data','countries.csv')
countries = read_csv(path_in)
countries = select(countries, iso3, continent, income_group)
data = merge(data, countries, by='iso3')

aggregated_by_continent  = data %>%
  group_by(year, climatescenario, probability, continent,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e3,1))
aggregated_by_continent = spread(aggregated_by_continent, percentile, cell_count)

aggregated_by_income  = data %>%
  group_by(year, climatescenario, probability, income_group,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e3,1))
aggregated_by_income = spread(aggregated_by_income, percentile, cell_count)
####

data_aggregated  = data %>%
  group_by(year, climatescenario, probability, #returnperiod,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e3,1))

hist = data_aggregated[data_aggregated$climatescenario == 'Historical', ]
data_aggregated = data_aggregated[data_aggregated$climatescenario != 'Historical', ]
hist = hist[hist$year == 'hist', ]
hist$year = "1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cell_count)

max_y_value = max(data_aggregated$mean)

plot1 =
  ggplot(data_aggregated,
         aes(x=probability, y=mean, fill=climatescenario)) +
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=data_aggregated, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.1,  color="#FF0000FF") +
  geom_text(data = data_aggregated, aes(label = paste(round(mean,1),"k")), size = 1.8,
            position = position_dodge(1), vjust =1.4, hjust =-0.2, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       # title = "Estimated Coastal Flooding Impact to Mobile Voice/Data Base Stations",
       # subtitle = "Reported by Annual Probability, Year, and Climate Scenario.",
       x = "Annual Probability", y = "Base Stations (Thousands)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value*1.2)) +
  facet_wrap(~year, ncol=4, nrow=1)

# data1$unit = 'sites_affected_thousands'
# data_aggregated$unit = 'costs_usd_billions'
# output = rbind(data1, data_aggregated)
# output = select(output, year, climatescenario, probability, unit, low, mean, high)
# dir.create(file.path(folder, 'report_data'), showWarnings = FALSE)
# filename = 'coastal_flooding_assets_and_costs_3.2.csv'
# path = file.path(folder, 'report_data', filename)
# write.csv(output, path)

data1 = data_aggregated

data_aggregated  = data %>%
  group_by(year, climatescenario, probability, #returnperiod,
           percentile) %>%
  summarise(cost_usd = round(sum(cost_usd_baseline)/1e9, 2))

hist = data_aggregated[data_aggregated$climatescenario == 'Historical', ]
data_aggregated = data_aggregated[data_aggregated$climatescenario != 'Historical', ]
hist = hist[hist$year == 'hist', ]
hist$year = "1980"
data_aggregated = rbind(data_aggregated, hist)

data_aggregated = spread(data_aggregated, percentile, cost_usd)

max_y_value = max(data_aggregated$mean)

plot2 = ggplot(data_aggregated,
               aes(x=probability, y=mean, fill=climatescenario)) +
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=data_aggregated, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.1,  color="#FF0000FF") +
  geom_text(aes(label = paste(round(mean,2),"Bn")), size = 1.8,
            position = position_dodge(1), vjust =1.4, hjust =-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       # title = "Estimated Coastal Flooding Damage Costs to Cellular Voice/Data Base Stations",
       # subtitle = "Reported by Annual Probability, Year, and Climate Scenario.",
       x = "Annual Probability", y = "Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value*1.2)) +
  facet_wrap(~year, ncol=4, nrow=1)

ggarrange(
  plot1,
  plot2,
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_coastal_flooding_impacts.png')
ggsave(path, units="in", width=8, height=6, dpi=600)

data1$unit = 'cells_vulnerable_thousands'
data_aggregated$unit = 'costs_usd_billions'
output = rbind(data1, data_aggregated)
output = select(output, year, climatescenario, probability, unit, low, mean, high)
dir.create(file.path(folder, 'report_data'), showWarnings = FALSE)
filename = 'fig_3.2_coastal_flooding_assets_and_costs.csv'
path = file.path(folder, 'report_data', filename)
write.csv(output, path)

data1$unit = 'cells_vulnerable_thousands'
data_aggregated$unit = 'costs_usd_billions'
output = rbind(data1, data_aggregated)
output = select(output, year, climatescenario, probability, unit, low, mean, high)
dir.create(file.path(folder, 'report_data'), showWarnings = FALSE)
filename = 'fig_3.2_coastal_flooding_assets_and_costs.csv'
path = file.path(folder, 'report_data', filename)
write.csv(output, path)

#####################
###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inunriver")

empty_df <- data.frame(iso3=character(),
                       # iso2=character(),
                       # country=character(),
                       # continent=character(),
                       # radio=character(),
                       # network=character(),
                       # cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       # cell_count_high=numeric(),
                       # cost_usd_low=numeric(),
                       cost_usd_baseline=numeric()#,
                       # cost_usd_high=numeric()
)

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

# data = data[(data$radio == 'LTE' | data$radio == 'UMTS'),]
# data = data[(data$radio == 'LTE'),]
# data = data[complete.cases(data[ , c('radio')]), ]

rm(empty_df, import_function)

# data$network = NULL

data = data %>%
  separate(file,
           into = c(
             "hazard_type",
             "climatescenario",
             "subsidence_model",
             "year",
             "returnperiod"),
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

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             "rp0002",
                             "rp0005",
                             "rp0010",
                             "rp0025",
                             "rp0050",
                             "rp0100",
                             "rp0250",
                             "rp0500",
                             "rp1000"
                           ),
                           labels=c(
                             "1-in-2-Years",
                             "1-in-5-Years",
                             "1-in-10-Years",
                             "1-in-25-Years",
                             "1-in-50-Years",
                             "1-in-100-Years",
                             "1-in-250-Years",
                             "1-in-500-Years",
                             "1-in-1000-Years"
                           )
)

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

# data$radio = factor(data$radio,
#                     levels=c("GSM","UMTS", "CDMA",
#                              "LTE","NR"),
#                     labels=c("2G GSM","3G UMTS", "3G UMTS",
#                              "4G LTE","5G NR"
#                     )
# )
# incomplete = data[!complete.cases(data), ]
data = data[complete.cases(data),]

# model_mean = data[data$subsidence_model == 'model-mean',]
# data = data[data$subsidence_model != 'model-mean',]

historical = data[data$subsidence_model == "000000000WATCH",]
data = data[data$subsidence_model != '000000000WATCH',]
historical$subsidence_model = factor(historical$subsidence_model,
                                     levels=c("000000000WATCH"),
                                     labels=c("Historical Baseline")
)

data$subsidence_model = factor(data$subsidence_model,
                               levels=c(
                                 "00000NorESM1-M",
                                 "0000GFDL-ESM2M",
                                 "0000HadGEM2-ES",
                                 "00IPSL-CM5A-LR",
                                 "MIROC-ESM-CHEM"),
                               labels=c(
                                 "00000NorESM1-M",
                                 "0000GFDL-ESM2M",
                                 "0000HadGEM2-ES",
                                 "00IPSL-CM5A-LR",
                                 "MIROC-ESM-CHEM"
                               )
)
data = select(data, iso3, #country, continent, radio,
              year, climatescenario, returnperiod,
              probability, cell_count_baseline, cost_usd_baseline)
# incomplete = data[!complete.cases(data), ]
data = data[complete.cases(data),]

####
folder = dirname(rstudioapi::getSourceEditorContext()$path)
path_in = file.path(folder, '..', 'data','countries.csv')
countries = read_csv(path_in)
countries = select(countries, iso3, continent, income_group)
data = merge(data, countries, by='iso3')

aggregated_by_continent  = data %>%
  group_by(year, climatescenario, probability, continent) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,3))
# aggregated_by_continent = spread(aggregated_by_continent, cell_count)

aggregated_by_income  = data %>%
  group_by(year, climatescenario, probability, income_group) %>%
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,3))
# aggregated_by_income = spread(aggregated_by_income, percentile, cell_count)
####





######################

inunriver = data %>%
  group_by(iso3, #country, continent, radio,
           year, climatescenario, returnperiod, probability) %>%
  summarize(
    low = min(cell_count_baseline),
    mean = round(mean(cell_count_baseline),1),
    high = max(cell_count_baseline)
  )
inunriver = inunriver %>% ungroup()

inunriver = select(inunriver, year, climatescenario, returnperiod,
                   probability, low, mean, high)
inunriver = gather(inunriver, "key", "value", low, mean, high)
inunriver = inunriver %>%
  group_by(year, climatescenario, probability, key) %>%
  summarize(value = sum(value))

historical_v2 = historical %>%
  group_by(year, climatescenario, probability) %>%
  summarize(
    key = 'mean',
    value = sum(cell_count_baseline)
  )
# historical = inunriver[inunriver$climatescenario == '000000000WATCH',]
# historical_v2 = historical
# historical_v2$key = "mean"
# historical_v2 = historical_v2[duplicated(historical_v2),]
# historical = rbind(historical, historical_v2)
# inunriver = inunriver[inunriver$climatescenario != 'Historical',]
inunriver = rbind(inunriver, historical_v2)

rm(historical_v2)

inunriver$value = inunriver$value/1e6
inunriver = spread(inunriver, key, value)

max_y_value = max(inunriver$mean)

plot1 = ggplot(inunriver,
               aes(x=probability, y=mean, fill=climatescenario)) +
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=inunriver,
                aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.1,  color="#FF0000FF") +
  geom_text(aes(label = paste(round(mean,2),"Mn")), size = 1.8,
            position = position_dodge(1), vjust =1.4, hjust=-.2, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=.8)) +
  labs(colour=NULL,
       # title = "Estimated Riverine Flooding Impact to Mobile Voice/Data Cells",
       # subtitle = "Reported by Annual Probability, Year, and Climate Scenario.",
       x = "Annual Probability", y = "Base Stations (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value*1.2)) +
  facet_wrap(~year, ncol=4, nrow=1)

####################

inunriver = data %>%
  group_by(iso3, #country, continent, radio,
           year, climatescenario, returnperiod, probability) %>%
  summarize(
    low = min(cost_usd_baseline),
    mean = round(mean(cost_usd_baseline),1),
    high = max(cost_usd_baseline)
  )
inunriver = inunriver %>% ungroup()

inunriver = select(inunriver, year, climatescenario, returnperiod,
                   probability, low, mean, high)
inunriver = gather(inunriver, "key", "value", low, mean, high)
inunriver = inunriver %>%
  group_by(year, climatescenario, probability, key) %>%
  summarize(value = sum(value))

historical_v2 = historical %>%
  group_by(year, climatescenario, probability) %>%
  summarize(
    key = 'mean',
    value = sum(cost_usd_baseline)
  )
# historical = inunriver[inunriver$climatescenario == '000000000WATCH',]
# historical_v2 = historical
# historical_v2$key = "mean"
# historical_v2 = historical_v2[duplicated(historical_v2),]
# historical = rbind(historical, historical_v2)
# inunriver = inunriver[inunriver$climatescenario != 'Historical',]
inunriver = rbind(inunriver, historical_v2)

rm(historical, historical_v2)

inunriver$value = inunriver$value/1e9
inunriver = spread(inunriver, key, value)

max_y_value = max(inunriver$mean)

plot2 =
  ggplot(inunriver,
         aes(x=probability, y=mean, fill=climatescenario)) +
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=inunriver,
                aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.1,  color="#FF0000FF") +
  geom_text(aes(label = paste(round(mean,1),"Bn")), size = 1.8,
            position = position_dodge(1), vjust =1.4, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       # title = "Estimated Riverine Flooding Impact to Mobile Voice/Data Base Stations",
       # subtitle = "Reported by Annual Probability, Year, and Climate Scenario.",
       x = "Annual Probability", y = "Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value*1.2)) +
  facet_wrap(~year, ncol=4, nrow=1)

ggarrange(
  plot1,
  plot2,
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_riverine_flooding_impacts.png')
ggsave(path, units="in", width=8, height=6, dpi=600)


########################################################
########################################################
#####Tropical storms
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="STORM")

empty_df <- data.frame(iso3=character(),
                       # iso2=character(),
                       # country=character(),
                       # continent=character(),
                       # radio=character(),
                       # network=character(),
                       # cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       # cell_count_high=numeric(),
                       # cost_usd_low=numeric(),
                       cost_usd_baseline=numeric()#,
                       # cost_usd_high=numeric()
)

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

# data = data[(data$radio != 'LTE' | data$radio != 'UMTS'),]
# data = data[complete.cases(data[ , c('radio')]), ]

rm(empty_df, import_function)

data = data %>%
  separate(file,
           into = c(
             "storm",
             "fixed",
             "return",
             "periods",
             "model",
             "rp",
             "year",
             "rp2"),
           sep = "_",
           convert = TRUE)

data$probability = ''
# data$probability[data$rp == 10] = "10%" # (1/10) * 100 = 50%
# data$probability[data$rp == 50] = "2%" # (1/50) * 100 = 10%
data$probability[data$rp == 100] = "1%" # (1/100) * 100 = 10%
data$probability[data$rp == 200] = "0.5%" # (1/200) * 100 = 4%
data$probability[data$rp == 500] = "0.2%" # (1/500) * 100 = 2%
data$probability[data$rp == 1000] = "0.1%" # (1/1000) * 100 = 1%
data$probability[data$rp == 10000] = "0.01%" # (1/10000) * 100 = .4%

###
folder = dirname(rstudioapi::getSourceEditorContext()$path)
path_in = file.path(folder, '..', 'data','countries.csv')
countries = read_csv(path_in)
countries = select(countries, iso3, continent, income_group)
data = merge(data, countries, by='iso3')

data = select(data, #iso3,
              continent,
              #cell_count_baseline,
              cell_count_baseline,
              model, probability)

data$probability = factor(data$probability,
                          levels=c('0.01%','0.1%', '0.2%','0.5%','1%'#,
                                   #'2%','10%'
                          )
)

data = data[
  data$probability == '0.01%' |
    data$probability == '0.1%' |
    data$probability == '0.2%' |
    data$probability == '0.5%' |
    data$probability == '1%',]

data = data[complete.cases(data),]

data$model = factor(data$model,
                    levels=c(
                      "constant",
                      "CMCC-CM2-VHR4",
                      "CNRM-CM6-1-HR",
                      "EC-Earth3P-HR",
                      "HadGEM3-GC31-HM"),
                    labels=c(
                      "Historical",
                      "CMCC-CM2-VHR4",
                      "CNRM-CM6-1-HR",
                      "EC-Earth3P-HR",
                      "HadGEM3-GC31-HM"),
)

data$continent <- factor(
  data$continent,
  levels = c("South America", "Oceania", "North America", "Europe", "Asia", "Africa")
)

data = data %>%
  group_by(continent, model, probability) %>%
  summarize(
    # low = min(cost_usd_baseline),
    cell_count_baseline = sum(cell_count_baseline),
    # high = max(cost_usd_baseline)
  )

data$year = '2050'
data$interaction = paste(data$probability, data$year)

data = select(data, interaction, continent, model, cell_count_baseline)
data$cell_count_baseline = data$cell_count_baseline/1e6

historical = data[data$model == 'Historical',]
data = data[data$model != 'Historical',]

data = data %>%
  group_by(interaction, continent) %>%
  summarize(
    low = round(min(cell_count_baseline),4),
    mean = round(mean(cell_count_baseline),4),
    high = round(max(cell_count_baseline),4)
  )

historical$interaction = factor(historical$interaction,
                                levels=c(
                                  "0.01% 2050",
                                  "0.1% 2050",
                                  "0.2% 2050",
                                  "0.5% 2050",
                                  "1% 2050"#,
                                  # "10% 2050",
                                  # "2% 2050"
                                ),
                                labels=c(
                                  "0.01% Historical",
                                  "0.1% Historical",
                                  "0.2% Historical",
                                  "0.5% Historical",
                                  "1% Historical"#,
                                  # "10% Historical",
                                  # "2% Historical"
                                ),
)

historical$low = NA
historical$mean = historical$cell_count_baseline
historical$high = NA
historical = historical %>% ungroup()
historical = select(historical, interaction, continent, low, mean, high)

data = rbind(data, historical)

data$interaction = factor(data$interaction,
                          levels=c(
                            "0.01% Historical",
                            "0.01% 2050",
                            "0.1% Historical",
                            "0.1% 2050",
                            "0.2% Historical",
                            "0.2% 2050",
                            "0.5% Historical",
                            "0.5% 2050",
                            "1% Historical",
                            "1% 2050"#,
                          ),
                          labels=c(
                            "0.01%\nHistorical",
                            "0.01%\n2050",
                            "0.1%\nHistorical",
                            "0.1%\n2050",
                            "0.2%\nHistorical",
                            "0.2%\n2050",
                            "0.5%\nHistorical",
                            "0.5%\n2050",
                            "1%\nHistorical",
                            "1%\n2050"#,
                          ),
)
filename = 'tropical_storm_data_figure_3.3.csv'
path_out = file.path(folder, 'report_data', filename)
write_csv(data, path_out)
rm(historical)

df_errorbar <-
  data |>
  group_by(continent, interaction) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction) |>
  summarize(
    continent = 'Africa',
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )

max_y_value = max(data$mean)

plot1 = ggplot(data,
               aes(x=interaction, y=mean, fill=continent)) +
  geom_bar(stat="identity", width=0.7) +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.05,  color="#FF0000FF") +
  geom_text(data = df_errorbar,
            aes(label = paste(round(mean, 2),"")), size = 2,#.25,
            vjust =-.7, hjust =-.5, angle = 0) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=0, hjust=.5)) +
  labs(colour=NULL,
       # title = "Estimated Tropical Cylone Impact to Mobile Voice/Data Base Stations",
       # subtitle = "Reported by Return Period, Climate Scenario and Continent.",
       x = "", y = "Base Stations (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Continent')) +
  scale_fill_manual(values = c("Africa" = "#000000","Asia" = "#E69F00",
      "Europe" = "#56B4E9","North America" = "#009E73","Oceania" = "#F0E442",
      "South America" = "#D55E00")) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+1.4))

data1 = data

# path = file.path(folder, 'figures', 'tropical_cyclone_impacts.png')
# ggsave(path, units="in", width=8, height=4.5, dpi=600)

########################################################
########################################################
#####Tropical storms
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="STORM")

empty_df <- data.frame(iso3=character(),
                       # iso2=character(),
                       # country=character(),
                       # continent=character(),
                       # radio=character(),
                       # network=character(),
                       # cell_count_low=numeric(),
                       cell_count_baseline=numeric(),
                       # cell_count_high=numeric(),
                       # cost_usd_low=numeric(),
                       cost_usd_baseline=numeric()#,
                       # cost_usd_high=numeric()
)

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

# data = data[(data$radio != 'LTE' | data$radio != 'UMTS'),]
# data = data[complete.cases(data[ , c('radio')]), ]

rm(empty_df, import_function)

data = data %>%
  separate(file,
           into = c(
             "storm",
             "fixed",
             "return",
             "periods",
             "model",
             "rp",
             "year",
             "rp2"),
           sep = "_",
           convert = TRUE)

data$probability = ''
# data$probability[data$rp == 10] = "10%" # (1/10) * 100 = 50%
# data$probability[data$rp == 50] = "2%" # (1/50) * 100 = 10%
data$probability[data$rp == 100] = "1%" # (1/100) * 100 = 10%
data$probability[data$rp == 200] = "0.5%" # (1/200) * 100 = 4%
data$probability[data$rp == 500] = "0.2%" # (1/500) * 100 = 2%
data$probability[data$rp == 1000] = "0.1%" # (1/1000) * 100 = 1%
data$probability[data$rp == 10000] = "0.01%" # (1/10000) * 100 = .4%

###
folder = dirname(rstudioapi::getSourceEditorContext()$path)
path_in = file.path(folder, '..', 'data','countries.csv')
countries = read_csv(path_in)
countries = select(countries, iso3, continent, income_group)
data = merge(data, countries, by='iso3')

data = select(data, #iso3,
              continent,
              #cell_count_baseline,
              cost_usd_baseline,
              model, probability)

data$probability = factor(data$probability,
                          levels=c('0.01%','0.1%', '0.2%','0.5%','1%'#,
                                   #'2%','10%'
                          )
)

data = data[
  data$probability == '0.01%' |
    data$probability == '0.1%' |
    data$probability == '0.2%' |
    data$probability == '0.5%' |
    data$probability == '1%',]

data = data[complete.cases(data),]

data$model = factor(data$model,
                    levels=c(
                      "constant",
                      "CMCC-CM2-VHR4",
                      "CNRM-CM6-1-HR",
                      "EC-Earth3P-HR",
                      "HadGEM3-GC31-HM"),
                    labels=c(
                      "Historical",
                      "CMCC-CM2-VHR4",
                      "CNRM-CM6-1-HR",
                      "EC-Earth3P-HR",
                      "HadGEM3-GC31-HM"),
)

data = data %>%
  group_by(continent, model, probability) %>%
  summarize(
    # low = min(cost_usd_baseline),
    cost_usd_baseline = mean(cost_usd_baseline),
    # high = max(cost_usd_baseline)
  )

data$year = '2050'
data$interaction = paste(data$probability, data$year)

data = select(data, interaction, continent, model, cost_usd_baseline)
data$cost_usd_baseline = data$cost_usd_baseline/1e9

historical = data[data$model == 'Historical',]
data = data[data$model != 'Historical',]

data = data %>%
  group_by(interaction, continent) %>%
  summarize(
    low = round(min(cost_usd_baseline),4),
    mean = round(mean(cost_usd_baseline),4),
    high = round(max(cost_usd_baseline),4)
  )

historical$interaction = factor(historical$interaction,
                                levels=c(
                                  "0.01% 2050",
                                  "0.1% 2050",
                                  "0.2% 2050",
                                  "0.5% 2050",
                                  "1% 2050"#,
                                  # "10% 2050",
                                  # "2% 2050"
                                ),
                                labels=c(
                                  "0.01% Historical",
                                  "0.1% Historical",
                                  "0.2% Historical",
                                  "0.5% Historical",
                                  "1% Historical"#,
                                  # "10% Historical",
                                  # "2% Historical"
                                ),
)

historical$low = NA
historical$mean = historical$cost_usd_baseline
historical$high = NA
historical = historical %>% ungroup()
historical = select(historical, interaction, continent, low, mean, high)

data = rbind(data, historical)

data$interaction = factor(data$interaction,
                          levels=c(
                            "0.01% Historical",
                            "0.01% 2050",
                            "0.1% Historical",
                            "0.1% 2050",
                            "0.2% Historical",
                            "0.2% 2050",
                            "0.5% Historical",
                            "0.5% 2050",
                            "1% Historical",
                            "1% 2050"#,
                          ),
                          labels=c(
                            "0.01%\nHistorical",
                            "0.01%\n2050",
                            "0.1%\nHistorical",
                            "0.1%\n2050",
                            "0.2%\nHistorical",
                            "0.2%\n2050",
                            "0.5%\nHistorical",
                            "0.5%\n2050",
                            "1%\nHistorical",
                            "1%\n2050"#,
                          ),
)

filename = 'tropical_storm_gdp_data_figure_3.3.csv'
path_out = file.path(folder, 'report_data', filename)
write_csv(data, path_out)
rm(historical)

# test = data %>%
#   group_by(interaction) %>%
#   summarize(
#     low = sum(low),
#     mean = sum(mean),
#     high = sum(high), 
#   )
# filename = 'cost_by_scenario.csv'
# path_out = file.path(folder, 'data', filename)
# write_csv(test, path_out)

df_errorbar <-
  data |>
  group_by(continent, interaction) |>
  summarize(
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  ) |>
  group_by(interaction) |>
  summarize(
    continent = 'Africa',
    low = sum(low),
    mean = sum(mean),
    high = sum(high)
  )

# max_y_value = max(data$mean)

plot2 = ggplot(data,
               aes(x=interaction, y=mean, fill=continent)) +
  geom_bar(stat="identity", width=0.7) +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.05,  color="#FF0000FF") +
  geom_text(data = df_errorbar,
            aes(label = paste(round(mean, 2),"")), size = 2,#.25,
            vjust =-.7, hjust =-.5, angle = 0) +
  # geom_text(aes(label = paste(round(mean,2),"Mn")), size = 1.8,
  #           position = position_dodge(1), vjust =.5, hjust =-.5, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=0, hjust=.5)) +
  labs(colour=NULL,
       # title = "Estimated Tropical Cylone Impact to Mobile Voice/Data Base Stations",
       # subtitle = "Reported by Return Period, Climate Scenario and Continent.",
       x = "", y = "Damage Cost (USD Bn)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Continent')) +
  scale_fill_manual(values = c("Africa" = "#000000","Asia" = "#E69F00",
      "Europe" = "#56B4E9","North America" = "#009E73","Oceania" = "#F0E442",
      "South America" = "#D55E00")) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, 2.4))

ggarrange(
  plot1,
  plot2,
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'global_tropical_storm_impacts.png')
ggsave(path, units="in", width=7, height=6, dpi=600)

data1$unit = 'cells_vulnerable_millions'
data$unit = 'costs_usd_billions'
output = rbind(data1, data)
output = select(output, interaction, continent, unit, low, mean, high)
dir.create(file.path(folder, 'report_data'), showWarnings = FALSE)
filename = 'fig_3.3_tropical_storm_assets_and_costs.csv'
path = file.path(folder, 'report_data', filename)
write.csv(output, path)
