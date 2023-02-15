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
data_directory = file.path(folder, '..','data','processed','results')
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
  group_by(hazard_type, climatescenario, year, probability) %>%
  summarize(
    cell_count_baseline = sum(cell_count_baseline),
    cost_usd_baseline = sum(cost_usd_baseline)
  )

write_csv(data, file.path(folder, 'rwanda.csv'))

