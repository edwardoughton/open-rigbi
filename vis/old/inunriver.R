## Visualization script for climate scenarios
library(tidyverse)
# library(ggpubr)
# install.packages("viridis")
# library(viridis)
install.packages("llply")
require(llply)
library(stringr)

###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results_v2')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inunriver")

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

rm(empty_df, import_function)

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

data$radio = factor(data$radio,
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data = data[data$subsidence_model != 'model-mean', ] 

data$subsidence_model = factor(data$subsidence_model,
                   levels=c("wtsub",
                            "000000000WATCH",
                            "00000NorESM1-M",
                            "0000GFDL-ESM2M",
                            "0000HadGEM2-ES",
                            "00IPSL-CM5A-LR",
                            "MIROC-ESM-CHEM"),
                   labels=c("RISES-AM",
                            "Historical Baseline",
                            "00000NorESM1-M",
                            "0000GFDL-ESM2M",
                            "0000HadGEM2-ES",
                            "00IPSL-CM5A-LR",
                            "MIROC-ESM-CHEM"
                   )
)

inunriver = data[data$hazard_type == 'inunriver',]

inunriver  = inunriver %>% 
  group_by(climatescenario, subsidence_model, year, 
           probability, returnperiod) %>% 
  summarise(cell_count = round(sum(cell_count_baseline)/1e6,2))

historical = inunriver[inunriver$year == '1980',]

hist_2030 = historical
hist_2030$year = "2030"
hist_2050 = historical
hist_2050$year = "2050"
hist_2080 = historical
hist_2080$year = "2080"

historical = rbind(hist_2030, hist_2050, hist_2080)

results = inunriver[inunriver$year != '1980',]

results = rbind(results, historical)

results_summary <- results %>%
  group_by(climatescenario, year, probability, returnperiod) %>%
  summarise(
    sd = sd(cell_count, na.rm = TRUE),
    cell_count = mean(cell_count)
  )


rm(historical, hist_2030, hist_2050, hist_2080)

max_y_value = max(inunriver$cell_count)


ggplot(results, aes(probability, cell_count, color = climatescenario)) +
  # geom_jitter(position = position_jitter(0.2)) + 
  geom_line(aes(group = climatescenario), data = results_summary) +
  geom_errorbar(aes(ymin = cell_count-sd, ymax = cell_count+sd), 
                data = results_summary, width = 0.2)+
  # scale_color_manual(values = c("#00AFBB", "#E7B800", "#E7B800")) +
  theme(legend.position = "bottom",
        axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
        # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, and Climate Scenario", 
       x = "Probability", y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=3, title='Scenario'),
         shape=guide_legend(ncol=3, title='Scenario'),
         color=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.02)) +
  facet_wrap(~year)

ggplot(results_summary, aes(probability, cell_count)) +
  geom_errorbar(
    aes(ymin = cell_count-sd, ymax = cell_count+sd, color = climatescenario),
    position = position_dodge(0.3), width = 0.2
  )+
  geom_point(aes(color = climatescenario), position = position_dodge(0.3)) +
  scale_color_manual(values = c("#00AFBB", "#E7B800", "#E7B800")) +  
  facet_wrap(~year)


ggplot(results_summary, aes(x=probability, y=cell_count, 
                      color=climatescenario, shape = subsidence_model
)
) +
  geom_point(position = position_dodge(width = .3)) +  
  facet_wrap(~year)






inunriver = rbind(inunriver, hist_2030)
inunriver = rbind(inunriver, hist_2050)
inunriver = rbind(inunriver, hist_2080)











inunriver$year = factor(inunriver$year,
                   levels=c("2030", "2050","2080"),
)







path = file.path(folder, 'figures', '1a_cell_count_aggregate_cell_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)











inuncoast = data[data$hazard_type == 'inuncoast',]

inuncoast  = inuncoast %>% 
  group_by(climatescenario, subsidence_model, year, 
           probability, returnperiod) %>% 
  summarise(cell_count = round(sum(cell_count)/1e6,2))

max_y_value = max(inuncoast$cell_count)

ggplot(inuncoast, aes(x=probability, y=cell_count, 
                    group=climatescenario, color=climatescenario)) +
  geom_line() +  
  theme(legend.position = "bottom",
        axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, and Climate Scenario", 
       x = "Probability", y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=3, title='Scenario'),
         shape=guide_legend(ncol=3, title='Scenario'),
         color=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.02)) +
  facet_wrap(~year)

path = file.path(folder, 'figures', '1a_cell_count_aggregate_cell_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)


# coastal$interaction = paste(coastal$year, coastal$climatescenario)
# unique(coastal$interaction)
# coastal$interaction = factor(coastal$interaction,
#                           levels=c(
#                             "hist historical",
#                             "2030 historical", 
#                             "2050 historical",
#                             "2080 historical",
#                             "2030 rcp4p5",
#                             "2050 rcp4p5",
#                             "2080 rcp4p5",
#                             "2030 rcp8p5",
#                             "2050 rcp8p5",
#                             "2080 rcp8p5"),
#                           labels=c("1980 Historical",
#                                    "2030 Historical",
#                                    "2050 Historical",
#                                    "2080 Historical",
#                                    "2030 RCP4.5",
#                                    "2030 RCP8.5",
#                                    "2050 RCP4.5",
#                                    "2050 RCP8.5",
#                                    "2080 RCP4.5",
#                                    "2080 RCP8.5")
# )



data$cell_count = (data$cell_count/1e6)

data = data[complete.cases(data),]

totals <- data %>%
  group_by(interaction, returnperiod) %>%
  summarize(value = signif(sum(cell_count), 2))

max_y_value = max(totals$value)

aggregate_cost = ggplot(data, aes(x=interaction, y=cell_count)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +
  labs(colour=NULL,
       title = "Estimated Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+.5)) +
  facet_wrap(~returnperiod)

path = file.path(folder, 'figures', '1a_cell_count_aggregate_cell_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)

###################
#####Aggregate cost
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

rm(empty_df, import_function)

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 

data  = data %>% 
  group_by(climatescenario, subsidence_model, year, 
           returnperiod, radio) %>% 
  summarise(cost_usd = sum(cost_usd))

data$interaction = paste(data$year, data$climatescenario)

data$interaction = factor(data$interaction,
                          levels=c(
                                   "1980 historical", 
                                   "hist historical",
                                   "2030 rcp4p5",
                                   "2050 rcp4p5",
                                   "2080 rcp4p5",
                                   "2030 rcp8p5",
                                   "2050 rcp8p5",
                                   "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                             ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                             )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$cost_usd = (data$cost_usd/1e9)

data = data[complete.cases(data),]

totals <- data %>%
  group_by(interaction, returnperiod) %>%
  summarize(value = round(sum(cost_usd), 0))

max_y_value = max(totals$value)

aggregate_cost = ggplot(data, aes(x=interaction, y=cost_usd)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
       subtitle = "Reported by Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Economic Damage ($US Billions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
    # expand_limits(y=0) +
    guides(linetype=guide_legend(ncol=2, title='Scenario'),
           shape=guide_legend(ncol=2, title='Scenario'),
           color=guide_legend(ncol=2, title='Scenario')) +
    scale_fill_viridis_d(direction=1) +
    scale_x_discrete(expand = c(0, 0.15)) +
    scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+20)) +
  facet_wrap(~returnperiod)
  
path = file.path(folder, 'figures', '1b_cost_aggregate_econ_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)

##################################
#####Aggregate cost by hazard type
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

data$network = NULL

rm(empty_df, import_function)

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(hazard_type, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>% 
  summarise(cell_count = sum(cell_count))

data$interaction = paste(data$year, data$climatescenario)

data$hazard_type = factor(data$hazard_type,
                          levels=c("inuncoast","inunriver"),
                          labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)


data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$cell_count = (data$cell_count/1e6)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(hazard_type, interaction, returnperiod) %>%
  summarize(value = signif(sum(cell_count), 2))

max_y_value = max(totals$value)

aggregate_cost = 
ggplot(data, aes(x=interaction, y=cell_count)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+.5)) +
  facet_wrap(hazard_type~returnperiod)

path = file.path(folder, 'figures', '2a_cell_count_damage_by_hazard.png')
ggsave(path, units="in", width=6, height=5, dpi=300)

##################################
#####Aggregate cost by hazard type
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

data$network = NULL

rm(empty_df, import_function)

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(hazard_type, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>% 
  summarise(cost_usd = sum(cost_usd))

data$interaction = paste(data$year, data$climatescenario)

data$hazard_type = factor(data$hazard_type,
                        levels=c("inuncoast","inunriver"),
                        labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)


data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$cost_usd = (data$cost_usd/1e9)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(hazard_type, interaction, returnperiod) %>%
  summarize(value = round(sum(cost_usd), 0))

max_y_value = max(totals$value)

aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cost_usd)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Economic Damage ($US Billions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+15)) +
  facet_wrap(hazard_type~returnperiod)

path = file.path(folder, 'figures', '2b_cost_aggregate_by_hazard_econ_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)

###################################
#####Aggregate cost by income group
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

rm(empty_df, import_function)

data$network = NULL

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$ï..country = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(income_group, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>%  #hazard_type, 
  summarise(cell_count = sum(cell_count))

data$interaction = paste(data$year, data$climatescenario)

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$income_group = factor(data$income_group,
                           levels=c("HIC", "UMC","LMC", "LIC"),
                           # levels=c("LIC", "LMC", "UMC", "HIC"),
                           # labels=c(
                           #   "Low-Income Country",
                           #   "Lower Middle-Income Country", 
                           #   "Upper Middle-Income Country", 
                           #   "High-Income Country")
                           labels=c(
                             "High-Income Countries",
                             "Upper Middle-Income Countries",
                             "Lower Middle-Income Countries", 
                             "Low-Income Countries"
                           )
)

data$cell_count = (data$cell_count/1e6)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(income_group, interaction, returnperiod) %>% #hazard_type, 
  summarize(value = signif(sum(cell_count), 2))

max_y_value = max(totals$value)

income_group_aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cell_count)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Income Group, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+1)) +
  facet_wrap(income_group~returnperiod)

path = file.path(folder, 'figures', '3a_cell_count_by_income_group_.png')
ggsave(path, units="in", width=6, height=5, dpi=300)

###################################
#####Aggregate cost by income group
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

rm(empty_df, import_function)

data$network = NULL

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$ï..country = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(income_group, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>%  #hazard_type, 
  summarise(cost_usd = sum(cost_usd))

data$interaction = paste(data$year, data$climatescenario)

# data$hazard_type = factor(data$hazard_type,
#                           levels=c("inuncoast","inunriver"),
#                           labels=c("Coastal Flooding", "Riverine Flooding")
# )

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$income_group = factor(data$income_group,
                          levels=c("HIC", "UMC","LMC", "LIC"),
                          # levels=c("LIC", "LMC", "UMC", "HIC"),
                          # labels=c(
                          #   "Low-Income Country",
                          #   "Lower Middle-Income Country", 
                          #   "Upper Middle-Income Country", 
                          #   "High-Income Country")
                          labels=c(
                            "High-Income Countries",
                            "Upper Middle-Income Countries",
                            "Lower Middle-Income Countries", 
                            "Low-Income Countries"
                            )
)

data$cost_usd = (data$cost_usd/1e9)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(income_group, interaction, returnperiod) %>% #hazard_type, 
  summarize(value = signif(sum(cost_usd), 2))

max_y_value = max(totals$value)

income_group_aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cost_usd)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
       subtitle = "Reported by Income Group, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Economic Damage ($US Billions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+25)) +
  facet_wrap(income_group~returnperiod)

path = file.path(folder, 'figures', '3b_cost_aggregate_income_group_econ_damage.png')
ggsave(path, units="in", width=6, height=5, dpi=300)


#########################################
#####Aggregate cell damage by hazard type
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

data$network = NULL

rm(empty_df, import_function)

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$ï..country = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(income_group, hazard_type, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>% 
  summarise(cell_count = sum(cell_count))

data$interaction = paste(data$year, data$climatescenario)

data$hazard_type = factor(data$hazard_type,
                          levels=c("inuncoast","inunriver"),
                          labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)


data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$income_group = factor(data$income_group,
                           levels=c("HIC", "UMC","LMC", "LIC"),
                           # levels=c("LIC", "LMC", "UMC", "HIC"),
                           # labels=c(
                           #   "Low-Income Country",
                           #   "Lower Middle-Income Country", 
                           #   "Upper Middle-Income Country", 
                           #   "High-Income Country")
                           labels=c(
                             "High-Income Countries",
                             "Upper Middle-Income Countries",
                             "Lower Middle-Income Countries", 
                             "Low-Income Countries"
                           )
)

data$cell_count = (data$cell_count/1e6)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(income_group, hazard_type, interaction, returnperiod) %>%
  summarize(value = signif(sum(cell_count), 2))

max_y_value = max(totals$value)

aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cell_count)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Damage to Cellular Voice/Data Cells",
       subtitle = "Reported by Income Group, Hazard, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Cells", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+.4)) +
  facet_wrap(income_group~hazard_type, nrow=2)

path = file.path(folder, 'figures', '4a_cell_count_by_hazard_income_group_cell_damage.png')
ggsave(path, units="in", width=8, height=5, dpi=300)


####################################
#####Aggregate cost by hazard type
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

data$network = NULL

rm(empty_df, import_function)

lut = read.csv(file.path(folder, 'income_group_lut.csv'))
lut$ï..country = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(income_group, hazard_type, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>% 
  summarise(cost_usd = sum(cost_usd))

data$interaction = paste(data$year, data$climatescenario)

data$hazard_type = factor(data$hazard_type,
                          levels=c("inuncoast","inunriver"),
                          labels=c("Coastal Flooding", "Riverine Flooding")
)

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)


data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$income_group = factor(data$income_group,
                           levels=c("HIC", "UMC","LMC", "LIC"),
                           # levels=c("LIC", "LMC", "UMC", "HIC"),
                           # labels=c(
                           #   "Low-Income Country",
                           #   "Lower Middle-Income Country", 
                           #   "Upper Middle-Income Country", 
                           #   "High-Income Country")
                           labels=c(
                             "High-Income Countries",
                             "Upper Middle-Income Countries",
                             "Lower Middle-Income Countries", 
                             "Low-Income Countries"
                           )
)

data$cost_usd = (data$cost_usd/1e9)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(income_group, hazard_type, interaction, returnperiod) %>%
  summarize(value = round(sum(cost_usd), 1))

max_y_value = max(totals$value)

aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cost_usd)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
       subtitle = "Reported by Income Group, Hazard, Forecast Year, Climate Scenario, and Technology", 
       x = NULL, y = "Economic Damage ($US Billions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+20)) +
  facet_wrap(income_group~hazard_type, nrow=2)

path = file.path(folder, 'figures', '4b_cost_aggregate_by_hazard_income_group_econ_damage.png')
ggsave(path, units="in", width=8, height=5, dpi=300)


################################
#####Aggregate cell damage by Continent
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

rm(empty_df, import_function)

data$network = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(continent, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>%  #hazard_type, 
  summarise(cell_count = sum(cell_count))

data$interaction = paste(data$year, data$climatescenario)

# data$hazard_type = factor(data$hazard_type,
#                           levels=c("inuncoast","inunriver"),
#                           labels=c("Coastal Flooding", "Riverine Flooding")
# )

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$continent = factor(data$continent,
                        # levels=c("Oceania", "South America", "North America", "Europe", "Asia", "Africa"),
                        levels=c("Africa","Asia","Europe","North America","South America","Oceania"),
                        labels=c("Africa","Asia","Europe","North America","South America","Oceania")
)

data$cell_count = (data$cell_count/1e6)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(continent, interaction, returnperiod) %>% #hazard_type, 
  summarize(value = signif(sum(cell_count), 2))

max_y_value = max(totals$value)

continent_aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cell_count)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
            position=position_stack(), 
            show.legend = FALSE
  ) +
  theme( legend.position = "bottom",
         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
         # text = element_text(size=8),
  ) +  
  labs(colour=NULL,
       title = "Estimated Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
       x = NULL, y = "Cells (Millions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+.5)) +
  facet_wrap(continent~returnperiod)

path = file.path(folder, 'figures', '5a_cell_count_continent_aggregate_cell_damage.png')
ggsave(path, units="in", width=8, height=5, dpi=300)


#####Aggregate cost by Continent
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

empty_df <- data.frame(iso3=character(),
                       iso2=character(), 
                       country=character(), 
                       continent=character(),
                       radio=character(),
                       # network=character(),
                       cell_count=numeric(),
                       cost_usd=numeric()) 

import_function = lapply(metric_files, function(x) {
  df <- read.csv(x, header = T, sep = ",")
  df_merge <- merge(empty_df, df, all = T)
  df_merge$file <- x
  return(df_merge)})

data <- do.call(rbind, import_function)

rm(empty_df, import_function)

data$network = NULL

data = merge(data, lut, by=c("iso3","iso3"))

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

data$returnperiod =  gsub(".csv", "", data$returnperiod) 
data$returnperiod =  gsub("rp0", "rp", data$returnperiod) 
data = data[complete.cases(data),]

data  = data %>% 
  group_by(continent, climatescenario, subsidence_model, year, 
           returnperiod, radio) %>%  #hazard_type, 
  summarise(cost_usd = sum(cost_usd))

data$interaction = paste(data$year, data$climatescenario)

# data$hazard_type = factor(data$hazard_type,
#                           levels=c("inuncoast","inunriver"),
#                           labels=c("Coastal Flooding", "Riverine Flooding")
# )

data$interaction = factor(data$interaction,
                          levels=c(
                            "1980 historical", 
                            "hist historical",
                            "2030 rcp4p5",
                            "2050 rcp4p5",
                            "2080 rcp4p5",
                            "2030 rcp8p5",
                            "2050 rcp8p5",
                            "2080 rcp8p5"),
                          labels=c("Historical",
                                   "Historical",
                                   "2030 RCP4.5",
                                   "2030 RCP8.5",
                                   "2050 RCP4.5",
                                   "2050 RCP8.5",
                                   "2080 RCP4.5",
                                   "2080 RCP8.5")
)

data$returnperiod = factor(data$returnperiod,
                           levels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "rp1000"
                           ),
                           labels=c(
                             # "100-year",
                             # "250-year",
                             # "500-year",
                             "1000-Year Return Period"
                           )
)

data$radio = factor(data$radio,
                    # levels=c("NR","LTE","UMTS",
                    #          "GSM"),
                    levels=c("GSM","UMTS",
                             "LTE","NR"),
                    # labels=c("5G NR","4G LTE",
                    #          "3G UMTS","2G GSM"
                    # )
                    labels=c("2G GSM","3G UMTS",
                             "4G LTE","5G NR"
                    )
)

data$continent = factor(data$continent,
 # levels=c("Oceania", "South America", "North America", "Europe", "Asia", "Africa"),
 levels=c("Africa","Asia","Europe","North America","South America","Oceania"),
 labels=c("Africa","Asia","Europe","North America","South America","Oceania")
)

data$cost_usd = (data$cost_usd/1e9)
data = data[complete.cases(data),]

totals <- data %>%
  group_by(continent, interaction, returnperiod) %>% #hazard_type, 
  summarize(value = round(sum(cost_usd), 1))

max_y_value = max(totals$value)

continent_aggregate_cost = 
  ggplot(data, aes(x=interaction, y=cost_usd)) +
  geom_bar(stat = "identity", aes(fill=radio)) + 
  geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
            size = 2, data = totals, vjust=-1, #hjust=1 ,
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
       x = NULL, y = "Economic Damage ($US Billions)", fill=NULL) +
  # scale_color_manual(values=c("#0072B2", "#D55E00")) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  # expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0,max_y_value+20)) +
  facet_wrap(continent~returnperiod)

path = file.path(folder, 'figures', '5b_cost_aggregate_continent_econ_damage.png')
ggsave(path, units="in", width=8, height=5, dpi=300)





























































# 
# 
# 
# 
# # ####################ECONOMIC
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder, '..','results', 'sites_affected_by_failures_GHA.csv'))
# 
# 
# data = select(data, floodtype, subsidence, year, returnperiod, climatescenario, technology, cost)
# 
# data  = data %>% 
#   group_by(floodtype, subsidence, year, returnperiod, climatescenario, technology) %>% 
#   summarise(cost = sum(cost))
# 
# wtsub = data[data$subsidence == "wtsub",] #remove inuncoast
# wtsub$subsidence = NULL
# model_mean = data[data$subsidence != "wtsub",] 
# 
# model_mean  = model_mean %>% 
#   group_by(floodtype, climatescenario, year, returnperiod, technology) %>% 
#   summarise(cost = mean(cost)) 
# 
# data = rbind(wtsub, model_mean) #historical
# 
# data$interaction = paste(data$year, data$climatescenario)
# 
# data$floodtype = factor(data$floodtype,
#                         levels=c("inuncoast","inunriver"),
#                         labels=c("Coastal Flooding", "Riverine Flooding")
# )
# 
# data$interaction = factor(data$interaction,
#                           levels=c("2030 rcp4p5",
#                                    "2050 rcp4p5",
#                                    "2080 rcp4p5",
#                                    "2030 rcp8p5",
#                                    "2050 rcp8p5",
#                                    "2080 rcp8p5"),
#                           labels=c("2030 RCP4.5",
#                                    "2030 RCP8.5",
#                                    "2050 RCP4.5",
#                                    "2050 RCP8.5",
#                                    "2080 RCP4.5",
#                                    "2080 RCP8.5")
# )
# 
# data$returnperiod = factor(data$returnperiod,
#                            levels=c("100-year","250-year",
#                                     "500-year","1000-year"),
#                            labels=c("100-year","250-year",
#                                     "500-year","1000-year")
# )
# 
# data$technology = factor(data$technology,
#                          levels=c("GSM","UMTS",
#                                   "LTE","NR"),
#                          labels=c("2G GSM","3G UMTS",
#                                   "4G LTE","5G NR")
# )
# 
# data$cost = (data$cost/1e6)
# 
# totals <- data %>%
#   group_by(floodtype, interaction, returnperiod) %>%
#   summarize(value = round(sum(cost), 1))
# 
# ggplot(data, aes(x=interaction, y=cost)) +
#   geom_bar(stat = "identity", aes(fill=technology)) + 
#   scale_color_manual(values=c("#0072B2", "#D55E00")) +
#   geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
#             size = 2, data = totals, vjust=-.5, #hjust=1 ,
#             position=position_stack(), 
#             show.legend = FALSE
#   ) +
#   theme( legend.position = "bottom",
#          axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
#          # text = element_text(size=8),
#   ) +
#   labs(colour=NULL,
#        title = "Estimated Economic Damage to Cellular Voice/Data Infrastructure",
#        subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
#        x = NULL, y = "Economic Damage ($US Millions)", fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines")) + 
#   expand_limits(y=0) +
#   guides(linetype=guide_legend(ncol=2, title='Scenario'),
#          shape=guide_legend(ncol=2, title='Scenario'),
#          color=guide_legend(ncol=2, title='Scenario')) +
#   scale_fill_viridis_d() +
#   # scale_x_discrete(expand = c(0, 0.15)) +
#   scale_y_continuous(expand = c(0, 0), limits=c(0,38)) +
#   facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)
# 
# path = file.path(folder, 'figures', 'GHA', 'GHA_overall_economic_cost_by_event.png')
# ggsave(path, units="in", width=8, height=5.5, dpi=300)
# 
# 
# # ####################SUPPLY-DEMAND METRICS
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder, '..', 'results', 'coverage_final_GHA.csv'))
# 
# data$interaction = paste(data$year, data$climatescenario)
# 
# data$floodtype = factor(data$floodtype,
#                         levels=c("inuncoast","inunriver"),
#                         labels=c("Coastal Flooding", "Riverine Flooding")
# )
# 
# data$interaction = factor(data$interaction,
#                           levels=c("2030 rcp4p5",
#                                    "2050 rcp4p5",
#                                    "2080 rcp4p5",
#                                    "2030 rcp8p5",
#                                    "2050 rcp8p5",
#                                    "2080 rcp8p5"),
#                           labels=c("2030 RCP4.5",
#                                    "2030 RCP8.5",
#                                    "2050 RCP4.5",
#                                    "2050 RCP8.5",
#                                    "2080 RCP4.5",
#                                    "2080 RCP8.5")
# )
# 
# data$returnperiod = factor(data$returnperiod,
#                            levels=c("100-year","250-year",
#                                     "500-year","1000-year"),
#                            labels=c("100-year","250-year",
#                                     "500-year","1000-year")
# )
# 
# data$technology = factor(data$technology,
#                          levels=c("GSM","UMTS",
#                                   "LTE","NR"),
#                          labels=c("2G GSM","3G UMTS",
#                                   "4G LTE","5G NR")
# )
# 
# data$covered_difference = data$covered_difference / 1e6
# 
# data = data[data$subsidence == "model_mean" |  data$subsidence == "wtsub",]
# 
# totals <- data %>%
#   group_by(floodtype, interaction, returnperiod) %>%
#   summarize(value = round(sum(covered_difference), 2))
# 
# ggplot(data, aes(x=interaction, y=covered_difference)) +
#   geom_bar(stat = "identity", aes(fill=technology)) + 
#   scale_color_manual(values=c("#0072B2", "#D55E00")) +
#   geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
#             size = 2, data = totals, vjust=-.5, #hjust=1 ,
#             position=position_stack(), 
#             show.legend = FALSE
#   ) +
#   theme(legend.position = "bottom",
#         axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8)) +
#   labs(colour=NULL,
#        title = "Mean Modeled Change in Population Coverage Against Historic Baseline",
#        subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
#        x = NULL, y = "Change in Population Coverage against the\nHistorical Baseline (Millions)", fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
#   guides(linetype=guide_legend(ncol=2, title='Scenario'),
#          shape=guide_legend(ncol=2, title='Scenario'),
#          color=guide_legend(ncol=2, title='Scenario')) +
#   scale_fill_viridis_d() +
#   # scale_x_discrete(expand = c(0, 0.15)) +
#   scale_y_continuous(expand = c(0.1, 0.1)) + #, limits=c(0,2)
#   facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)
# 
# path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_difference.png')
# ggsave(path, units="in", width=8, height=5.5, dpi=300)
# 
# ########################################################################
# 
# 
# # ####################SUPPLY-DEMAND METRICS
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder, '..', 'results', 'econ_final_GHA.csv'))
# 
# data$interaction = paste(data$year, data$climatescenario)
# 
# data$floodtype = factor(data$floodtype,
#                         levels=c("inuncoast","inunriver"),
#                         labels=c("Coastal Flooding", "Riverine Flooding")
# )
# 
# data$interaction = factor(data$interaction,
#                           levels=c("2030 rcp4p5",
#                                    "2050 rcp4p5",
#                                    "2080 rcp4p5",
#                                    "2030 rcp8p5",
#                                    "2050 rcp8p5",
#                                    "2080 rcp8p5"),
#                           labels=c("2030 RCP4.5",
#                                    "2030 RCP8.5",
#                                    "2050 RCP4.5",
#                                    "2050 RCP8.5",
#                                    "2080 RCP4.5",
#                                    "2080 RCP8.5")
# )
# 
# data$returnperiod = factor(data$returnperiod,
#                            levels=c("100-year","250-year",
#                                     "500-year","1000-year"),
#                            labels=c("100-year","250-year",
#                                     "500-year","1000-year")
# )
# 
# data$technology = factor(data$technology,
#                          levels=c("GSM","UMTS",
#                                   "LTE","NR"),
#                          labels=c("2G GSM","3G UMTS",
#                                   "4G LTE","5G NR")
# )
# 
# data$cost_difference = data$cost_difference / 1e6
# 
# data = data[data$subsidence == "model_mean" |  data$subsidence == "wtsub",]
# 
# totals <- data %>%
#   group_by(floodtype, interaction, returnperiod) %>%
#   summarize(value = round(sum(cost_difference), 1))
# 
# ggplot(data, aes(x=interaction, y=cost_difference)) +
#   geom_bar(stat = "identity", aes(fill=technology)) + 
#   scale_color_manual(values=c("#0072B2", "#D55E00")) +
#   geom_text(aes(x=interaction, y=value, label=value), #, color="#ffffff"
#             size = 2, data = totals, vjust=-.5, #hjust=1 ,
#             position=position_stack(), 
#             show.legend = FALSE
#   ) +
#   theme( legend.position = "bottom",
#          axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1, size=8),
#          # text = element_text(size=8),
#   ) +
#   labs(colour=NULL,
#        title = "Mean Modeled Change in Estimated Economic Damage Against Historic Baseline",
#        subtitle = "Reported by Hazard, Forecast Year, Climate Scenario, Return Period and Technology", 
#        x = NULL, y = "Change in Flooding Damage Costs against the\nHistorical Baseline (Millions)", fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
#   guides(linetype=guide_legend(ncol=2, title='Scenario'),
#          shape=guide_legend(ncol=2, title='Scenario'),
#          color=guide_legend(ncol=2, title='Scenario')) +
#   scale_fill_viridis_d() +
#   scale_y_continuous(expand = c(0.1, 0.1)) + #, limits=c(0,2)
#   facet_wrap(floodtype~returnperiod, scales = "free_y", ncol=4)
# 
# path = file.path(folder, 'figures', 'GHA', 'GHA_econ_cost_against_baseline.png')
# ggsave(path, units="in", width=8, height=5.5, dpi=300)
# 
# # ####################COVERAGE BY DECILES
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder,'..','data','processed','GHA', 'coverage_by_decile.csv'))
# 
# # data$population[data$technology == "NR" | data$decile == 10 | data$covered == 0] <- 0
# 
# data$covered = factor(data$covered,
#                       levels=c(1,0),
#                       labels=c("Covered","Uncovered")
# )
# 
# data$technology = factor(data$technology,
#                          levels=c('GSM', 'UMTS', 'LTE', 'NR'),
#                          labels=c("2G GSM","3G UMTS", "4G LTE", "5G NR")
# )
# 
# data$decile = factor(data$decile,
#                      levels=c(10,20,30,40,50,60,70,80,90,100),
#                      labels=c('0 -\n10%','10 -\n20%','20 -\n30%','30 -\n40%',
#                               '40 -\n50%','50 -\n60%',
#                               '60 -\n70%','70 -\n80%','80 -\n90%','90 -\n100%'))
# 
# data$population = data$population / 1e6
# 
# totals <- data %>%
#   group_by(decile, covered, technology) %>%
#   summarize(value2 = round(population, 1))
# 
# # totals$value2[totals$technology == "5G NR" | totals$covered == "uncovered" | totals$decile == "0-10"] <- 0
# 
# plot1 = ggplot(data, aes(x=factor(decile), y=population, fill=covered)) +
#   geom_bar(stat="identity", position=position_dodge()) +
#   geom_text(aes(ymax=0, x=decile, y=value2 + 1, label=value2), #, color="#ffffff"
#             size = 2.25, data = totals, vjust=1, #hjust=1 ,
#             position=position_dodge(width = 1), show.legend = FALSE
#   ) +
#   theme(legend.position = "bottom") +
#   labs(colour=NULL,
#        title = "(A) Population Coverage by Population Density Decile and Technology",
#        subtitle = "Coverage is defined as a Signal-to-Interference-plus-Noise-Ratio (SINR) >0 dB",
#        x = 'Population Density Decile\n(0-10% contains the most populated 10% of 1 km^2 tiles)',
#        y = "Population Coverage (Millions)",
#        fill=NULL, color=NULL) +
#   theme(panel.spacing = unit(0.6, "lines"),
#         axis.text.x = element_text(angle = 15, hjust=1)) +
#   expand_limits(y=0) +
#   guides() +
#   scale_y_continuous(expand = c(0, 0), limits = c(0, 17.5)) +
#   scale_fill_viridis_d(direction=1) +
#   facet_wrap(~technology)
# 
# # path = file.path(folder, 'figures', 'GHA', 'GHA_coverage_by_deciles.png')
# # ggsave(path, units="in", width=8, height=6, dpi=300)
# 
# # ####################COVERAGE BY DECILES
# folder <- dirname(rstudioapi::getSourceEditorContext()$path)
# 
# data <- read.csv(file.path(folder,'..','data','processed','GHA', 'coverage_by_decile.csv'))
# 
# # data$population[data$technology == "NR" | data$decile == 10 | data$covered == 0] <- 0
# 
# data$covered = factor(data$covered,
#                       levels=c(0, 1),
#                       labels=c("Uncovered", "Covered")
# )
# 
# data$technology = factor(data$technology,
#                          levels=c('GSM', 'UMTS', 'LTE', 'NR'),
#                          labels=c("2G GSM","3G UMTS", "4G LTE", "5G NR")
# )
# 
# data$decile = factor(data$decile,
#                      levels=c(10,20,30,40,50,60,70,80,90,100),
#                      labels=c('0 -\n10%','10 -\n20%','20 -\n30%','30 -\n40%',
#                               '40 -\n50%','50 -\n60%',
#                               '60 -\n70%','70 -\n80%','80 -\n90%','90 -\n100%'))
# 
# data = data %>%
#   group_by(technology,decile) %>%
#   mutate(countT= sum(population)) %>%
#   group_by(covered) %>%
#   mutate(perc=round(100*population/countT))
# 
# plot2 = ggplot(data, aes(x=factor(decile), y=perc, fill=covered)) +
#   geom_bar(stat="identity") +
#   geom_text(aes(x=decile, y=perc, label = paste0(perc,"%")),#, color="#ffffff"
#             size = 2.25, data = data, vjust=-.75, hjust=.5, 
#             show.legend = FALSE, position = position_stack(),
#   ) +
#   theme(legend.position = "bottom") +
#   labs(colour=NULL,
#        title = "(B) Percentage Population Coverage by Population Density Decile and Technology",
#        subtitle = "Coverage is defined as a Signal-to-Interference-plus-Noise-Ratio (SINR) >0 dB",
#        x = 'Population Density Decile\n(0-10% contains the most populated 10% of 1 km^2 tiles)',
#        y = "Population Coverage (%)",
#        fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines"),
#         axis.text.x = element_text(angle = 15, hjust=1)) +
#   expand_limits(y=0) +
#   guides(linetype=guide_legend(ncol=2, title='Scenario'),
#          shape=guide_legend(ncol=2, title='Scenario'),
#          color=guide_legend(ncol=2, title='Scenario')) +
#   scale_y_continuous(expand = c(0, 0), limits = c(0, 100)) +
#   scale_fill_viridis_d(direction=-1) +
#   facet_wrap(~technology)
# 
# ############
# ggarrange(
#   plot1,
#   plot2,
#   # labels = c("A", "B"),
#   common.legend = TRUE,
#   legend = 'bottom',
#   ncol = 1, nrow = 2)
# 
# path = file.path(folder, 'figures', 'GHA', 'GHA_panel_plot.png')
# ggsave(path, units="in", width=8, height=10, dpi=300)
# 
# 
# 
# 
# 
# 
# 
