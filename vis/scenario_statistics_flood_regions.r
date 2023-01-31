## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

###################
#####Aggregate cells
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data$mean_depth = gsub("-", 'NA', data$mean_depth)
data$max_depth = gsub("-", 'NA', data$max_depth)
data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)

data$mean_depth = as.numeric(as.character(data$mean_depth))
data$max_depth = as.numeric(as.character(data$max_depth))
data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))

country_info = read_csv(file.path(folder, '..', 'data','raw', 'countries.csv'))
country_info = select(country_info, iso3, flood_region)

data = merge(data,country_info,by="iso3")

data = data %>%
  group_by(hazard, flood_region, #income_group, 
           climate_scenario, model, year, 
           return_period, percentile) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    # max_depth = max(max_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE)
  )
data = data %>% ungroup()

write_csv(data, 'flood_region_scenario_stats.csv')

data = data[data$hazard == 'inunriver',]
data = data[data$model == 'MIROC-ESM-CHEM',]
data = data[data$return_period == 'rp01000',]

data = data[
  data$climate_scenario == 'historical' | 
    data$climate_scenario == 'rcp4p5' | 
    data$climate_scenario == "rcp8p5",]

data$climate_scenario = factor(data$climate_scenario,
                              levels=c("historical","rcp4p5","rcp8p5"),
                              labels=c("Historical","RCP4.5","RCP8.5")
)

data = select(data, flood_region, climate_scenario, year, flooded_area_km2)

data$flooded_area_km2 = data$flooded_area_km2 / 1e6

ggplot(data, aes(x=year, y=flooded_area_km2, 
                 group=climate_scenario, color=climate_scenario)) + 
  geom_line(aes(linetype=climate_scenario))+
  geom_point(aes(shape=climate_scenario)) +
  facet_wrap(~flood_region) #, ncol=4, nrow=1



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

