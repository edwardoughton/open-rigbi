## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
# install.packages("viridis")
# library(viridis)
install.packages("llply")
require(llply)
library(stringr)

###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, 'results')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="inuncoast")

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

data = data[data$subsidence_model != 'nosub', ] 
data$subsidence_model = NULL

data = data %>%
  mutate_at(vars(percentile), ~replace_na(., "high"))
# unique(data$percentile)
data$percentile = gsub("05.csv", "low", data$percentile)
data$percentile = gsub("50.csv", "mean", data$percentile)
data$percentile[data$climatescenario == 'Historical'] <- 'mean'  

# unique(data$percentile)
data$zero = NULL
data$perc = NULL
# table(data$percentile)
# table(data$year)

# data$interaction = paste(data$probability, data$climatescenario)
# 
# data$interaction = factor(data$interaction,
#                     levels=c(
#                        "0.1% Historical","0.1% RCP4.5", "0.1% RCP8.5",
#                        "0.2% Historical","0.2% RCP4.5", "0.2% RCP8.5",
#                        "0.4% Historical","0.4% RCP4.5", "0.4% RCP8.5",
#                        "1% Historical","1% RCP4.5", "1% RCP8.5"
#                              )#,
#                     # labels=c("2G GSM","3G UMTS",
#                     #          "4G LTE","5G NR"
#                     # )
# )

# data_all  = data %>%
#   group_by(interaction, year, #probability, returnperiod,
#            radio, 
#            percentile) %>%
#   summarise(cell_count = round(sum(cell_count)/1e6,2))
# data_all = data_all[data_all$percentile == 'mean', ] 

data_aggregated  = data %>%
  group_by(year, climatescenario, probability, #returnperiod,
           percentile) %>%
  summarise(cell_count = round(sum(cell_count)/1e6,2))

data_aggregated = data_aggregated[data_aggregated$year != 'hist', ] 

data_aggregated = spread(data_aggregated, percentile, cell_count)

max_y_value = max(data_aggregated$mean)

test1 = ggplot(data_aggregated, 
               aes(x=probability, y=mean, fill=climatescenario)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=data_aggregated, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.7,  color="#FF0000FF") +
  geom_text(aes(label = paste(round(mean,2),"mn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.5, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, and Climate Scenario", 
       x = "Annual Probability", y = "Cells (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4)) +
  facet_wrap(~year)
  

data_aggregated  = data %>%
  group_by(year, climatescenario, probability, #returnperiod,
           percentile) %>%
  summarise(cost_usd = round(sum(cost_usd)/1e9,1))

data_aggregated = data_aggregated[data_aggregated$year != 'hist', ] 

data_aggregated = spread(data_aggregated, percentile, cost_usd)

max_y_value = max(data_aggregated$mean)

test2 = ggplot(data_aggregated, 
               aes(x=probability, y=mean, fill=climatescenario)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_errorbar(data=data_aggregated, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.7,  color="#FF0000FF") +
  geom_text(aes(label = paste(round(mean,2),"bn")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust =-.7, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Damage Costs to Cellular Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, and Climate Scenario", 
       x = "Annual Probability", y = "Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=3, title='Scenario')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+20)) +
  facet_wrap(~year)

ggarrange(
  test1, 
  test2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'test1.png')
ggsave(path, units="in", width=8, height=6, dpi=300)

