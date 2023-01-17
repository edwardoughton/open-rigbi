## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data = data %>%
  group_by(hazard, income_group, climate_scenario, model, year, 
           return_period, percentile) %>%
  summarize(
    mean_depth = mean(mean_depth),
    max_depth = max(max_depth),
    flooded_area_km2 = sum(flooded_area_km2)
  )

data = data[data$percentile != 5,]

write_csv(data, 'global_scenario_stats.csv')

data = data[data$hazard == 'inuncoast',]

data = data[
  data$climate_scenario == 'historical' | 
    data$climate_scenario == 'rcp4p5' | 
    data$climate_scenario == "rcp8p5",]

data$climate_scenario = factor(data$climate_scenario,
                              levels=c("historical","rcp4p5","rcp8p5"),
                              labels=c("Historical","RCP4.5","RCP8.5")
)

data$return_period = factor(data$return_period,
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

# unique(data$return_period)
# #replace return periods
# data$return_period =  gsub("rp0002", "rp0002", data$return_period)
# data$return_period =  gsub("rp0005", "rp0005", data$return_period)
# data$return_period =  gsub("rp0010", "rp0010", data$return_period)
# data$return_period =  gsub("rp0025", "rp0025", data$return_period)
# data$return_period =  gsub("rp0050", "rp0050", data$return_period)
# data$return_period =  gsub("rp0100", "rp0100", data$return_period)
# data$return_period =  gsub("rp0250", "rp0250", data$return_period)
# data$return_period =  gsub("rp0500", "rp0500", data$return_period)
# data$return_period =  gsub("rp1000", "rp1000", data$return_period)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$return_period == "1-in-2-Years"] = "50%" # (1/2) * 100 = 50%
data$probability[data$return_period == "1-in-5-Years"] = "20%" # (1/10) * 100 = 10%
data$probability[data$return_period == "1-in-10-Years"] = "10%" # (1/10) * 100 = 10%
data$probability[data$return_period == "1-in-25-Years"] = "4%" # (1/25) * 100 = 4%
data$probability[data$return_period == "1-in-50-Years"] = "2%" # (1/50) * 100 = 2%
data$probability[data$return_period == "1-in-100-Years"] = "1%" # (1/100) * 100 = 1%
data$probability[data$return_period == "1-in-250-Years"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$return_period == "1-in-500-Years"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$return_period == "1-in-1000-Years"] = "0.1%" # (1/1000) * 100 = .1%





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

data = data[data$model != 'nosub', ]

# data$subsidence_model = NULL
# unique(data$percentile)
# low = data[data$percentile == "05",] #5th percentile
# mean = data[data$percentile == "50",] #50th percentile
# high = data[data$percentile == "0",] #95th percentile
# odd = data[data$percentile == "5",] #mistake

data$interaction = paste(data$climate_scenario, data$year)
data = data[data$interaction != 'Historical 2030',] 
data = data[data$interaction != 'Historical 2050',] 
data = data[data$interaction != 'Historical 2080',] 
write_csv(data, 'test1.csv')
data$interaction = factor(data$interaction,
                          levels=c(
                            "Historical hist",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
                          labels = c(
                            "Historical 1980",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"
                          )
)
write_csv(data, 'test2.csv')
data$percentile = gsub("05", "low", data$percentile)
data$percentile = gsub("50", "mean", data$percentile)
data$percentile = gsub("0", "high", data$percentile)
data$percentile[data$climate_scenario == 'Historical'] <- 'mean'  

data$zero = NULL
data$perc = NULL

data = data %>% ungroup()

data = select(data, income_group, interaction, probability, percentile, 
              flooded_area_km2) #mean_depth, 


data$income_group = factor(data$income_group,
                           levels=c(
                             "LIC",
                             "LMC",
                             "UMC",
                             "HIC"))
data = data[complete.cases(data),]

# test = data[data$probability == "1%",]

data$flooded_area_km2 = data$flooded_area_km2 #/ 1e6
data_aggregated = spread(data, percentile, flooded_area_km2)
# 
# data_aggregated$high[data_aggregated$interaction == 'Historical 1980' & 
#                      data_aggregated$income_group == 'LIC'] <- data_aggregated$mean
# data_aggregated$high[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'LMC'] <- data_aggregated$mean
# data_aggregated$high[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'UMC'] <- data_aggregated$mean
# data_aggregated$high[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'HIC'] <- data_aggregated$mean
# data_aggregated$low[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'LIC'] <- data_aggregated$mean
# data_aggregated$low[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'LMC'] <- data_aggregated$mean
# data_aggregated$low[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'UMC'] <- data_aggregated$mean
# data_aggregated$low[data_aggregated$interaction == 'Historical 1980' & 
#                        data_aggregated$income_group == 'HIC'] <- data_aggregated$mean

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

max_y_value = data_aggregated %>%
  group_by(interaction, probability) %>%
  summarize(
    max_y_value = sum(high)
  )
max_y_value = max(max_y_value$max_y_value, na.rm = T)


# plot1 = 
ggplot(data_aggregated, 
       aes(x=interaction, y=mean, fill=income_group)) + 
  geom_bar(stat="identity", position='stack') +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.4,  color="#FF0000FF") +
  # geom_text(data = df_errorbar, aes(label = paste(round(mean,2),"Mn")), size = 1.8,
  #           position = position_dodge(1), vjust =.5, hjust =-.7, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Coastal Flooding Impact to Mobile Voice/Data Cells",
       subtitle = "Reported by Annual Probability, Year, and Climate Scenario.", 
       x = "Annual Probability", y = "Flooded Area (Millions km^2)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Scenario')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, 200000)) + #max_y_value+(max_y_value/5)
  facet_wrap(~probability) #, ncol=4, nrow=1

