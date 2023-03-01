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
data_directory = file.path(folder, 'results_v5')
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

data$network = NULL

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
                    levels=c("GSM","UMTS", "CDMA",
                             "LTE","NR"),
                    labels=c("2G GSM","3G UMTS", "3G UMTS",
                             "4G LTE","5G NR"
                    )
)
# incomplete = data[!complete.cases(data), ] 
data = data[complete.cases(data),]

data = data[(data$year == 1980 | data$year == 2080),]
data = data[(data$probability == "0.1%"),]

data$radio = factor(data$radio,
                    levels=c(
                      "2G GSM",
                      "3G UMTS",
                      "4G LTE",
                      "5G NR"
                    ),
                    labels=c(
                      "2G GSM",
                      "3G UMTS",
                      "4G LTE",
                      "5G NR"
                    )
)

data$continent = factor(data$continent,
                        levels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North America",
                          "Oceania",
                          "South America"
                        ),
                        labels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North\nAmerica",
                          "Oceania",
                          "South\nAmerica"
                        )
)

# test = data[(data$year == 1980 & data$probability == "0.1%"),]
# sum(test$cell_count_baseline) #9339916 cells

country_info = read_csv(file.path(folder, '..', 'data','raw', 'countries.csv'))
country_info = select(country_info, iso3, flood_region)
data = merge(data, country_info,by="iso3")


data$flood_region = factor(data$flood_region,
                           levels=c(
                             "Brazil",
                             "Central America & Caribbean",
                             "China",
                             "Japan & Korea",
                             "Middle East & North Africa",
                             "North America",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "South America",
                             "South Asia",
                             "Southeast Asia",
                             "Sub-Saharan Africa",
                             "Western Europe"
                           ),
                           labels=c(
                             "Brazil",
                             "Central America\n& Caribbean",
                             "China",
                             "Japan\n& Korea",
                             "Middle East\n& North Africa",
                             "North\nAmerica",
                             "Oceania",
                             "Rest of\nFSU",
                             "Russia",
                             "South\nAmerica",
                             "South\nAsia",
                             "Southeast\nAsia",
                             "Sub-Saharan\nAfrica",
                             "Western\nEurope"
                           )
)

# model_mean = data[data$subsidence_model == 'model-mean',]
data = data[data$subsidence_model != 'model-mean',]

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

data = select(data, iso3, country, continent, flood_region, radio, 
              year, climatescenario, #returnperiod, 
              probability, cell_count_baseline, #cost_usd_baseline
              )

data = data[complete.cases(data),]

#########################

data_continent = data %>%
  group_by(iso3, country, continent, radio, climatescenario) %>%
  summarize(
    cell_count_baseline = round(mean(cell_count_baseline),3)
  )

historical_continent = select(historical, iso3, country, continent, radio, 
                    # year, 
                    climatescenario, #returnperiod, 
                    # probability, 
                    cell_count_baseline, #cost_usd_baseline
)

data_continent = rbind(data_continent, historical_continent)

data_continent = data_continent %>%
  group_by(continent, radio, climatescenario) %>%
  summarize(
    count = round(sum(cell_count_baseline)/1e6,3)
  )

#########################

data_region = data %>%
  group_by(iso3, country, flood_region, radio, climatescenario) %>%
  summarize(
    cell_count_baseline = round(mean(cell_count_baseline),2)
  )

historical_region = select(historical, iso3, country, flood_region, radio, 
                              # year, 
                              climatescenario, #returnperiod, 
                              # probability, 
                              cell_count_baseline, #cost_usd_baseline
)

data_region = rbind(data_region, historical_region)

data_region = data_region %>%
  group_by(flood_region, radio, climatescenario) %>%
  summarize(
    count = round(sum(cell_count_baseline)/1e6,2)
  )

#########################

historical_data = data_continent[(data_continent$climatescenario == 'Historical'),]

sum(historical_data$count) #9.3 m cells

max_y_value = max(historical_data$count, na.rm=TRUE)

historical_continent = 
  ggplot(historical_data, 
         aes(x=continent, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
      position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Continent (Climate Scenario: Historical)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))

historical_data = data_region[(data_region$climatescenario == 'Historical'),]

sum(historical_data$count) #9.3 m cells

max_y_value = max(historical_data$count, na.rm=TRUE)

historical_region = 
  ggplot(historical_data, 
         aes(x=flood_region, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Flood Region (Climate Scenario: Historical)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))

#########################

rcp4p5 = data_continent[(data_continent$climatescenario == 'RCP4.5'),]

sum(rcp4p5$count) #46.53 m cells

max_y_value = max(rcp4p5$count, na.rm=TRUE)

rcp4p5_continent = 
  ggplot(rcp4p5, 
         aes(x=continent, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Continent (Climate Scenario: RCP4.5)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))

rcp4p5 = data_region[(data_region$climatescenario == 'RCP4.5'),]

sum(rcp4p5$count) #46.53 m cells

max_y_value = max(rcp4p5$count, na.rm=TRUE)

rcp4p5_region = 
  ggplot(rcp4p5, 
         aes(x=flood_region, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Flood Region (Climate Scenario: RCP4.5)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))

#########################

rcp8p5 = data_continent[(data_continent$climatescenario == 'RCP8.5'),]

sum(rcp8p5$count) #46.53 m cells

max_y_value = max(rcp8p5$count, na.rm=TRUE)

rcp8p5_continent = 
  ggplot(rcp8p5, 
         aes(x=continent, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Continent (Climate Scenario: RCP8.5)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))

rcp8p5 = data_region[(data_region$climatescenario == 'RCP8.5'),]

sum(rcp8p5$count) #46.53 m cells

max_y_value = max(rcp8p5$count, na.rm=TRUE)

rcp8p5_region = 
  ggplot(rcp8p5, 
         aes(x=flood_region, y=count, fill=radio)) + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,4),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Riverine Damaged Mobile Voice/Data Cells by Flood Region (Climate Scenario: RCP8.5)",
       subtitle = "Reported by  cellular generation for an event annual probability of 0.1%.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.4))


ggarrange(
  historical_continent, 
  rcp4p5_continent,
  rcp8p5_continent,
  labels = c("A", "B", "C"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 3)

path = file.path(folder, 'figures', 'cell_count_damage_1000_continent.png')
ggsave(path, units="in", width=8, height=8, dpi=300)

ggarrange(
  historical_region, 
  rcp4p5_region,
  rcp8p5_region,
  labels = c("A", "B", "C"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 3)

path = file.path(folder, 'figures', 'cell_count_damage_1000_region.png')
ggsave(path, units="in", width=8, height=8, dpi=300)

