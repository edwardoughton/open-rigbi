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
data_directory = file.path(folder, 'results_v3')
setwd(data_directory)

metric_files <- list.files(data_directory, pattern="STORM")

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

data = select(data, #iso3, 
              continent, 
              #cell_count_baseline, 
              cost_usd_baseline, 
              model, probability)
# unique(data$probability)
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
    cost_usd_baseline = sum(cost_usd_baseline),
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
)

write_csv(data, 'tropical_storm_data.csv')

rm(test, historical)

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

# plot1 = 
  ggplot(data, 
       aes(x=interaction, y=mean, fill=continent)) + 
  geom_bar(stat="identity") +
  geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
                position = position_dodge(1),
                lwd = 0.2,
                show.legend = FALSE, width=0.7,  color="#FF0000FF") +
  # geom_text(aes(label = paste(round(mean,2),"Mn")), size = 1.8,
  #           position = position_dodge(1), vjust =.5, hjust =-.5, angle = 90)+
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=45, hjust=1)) +
  labs(colour=NULL,
       title = "Estimated Tropical Cylone Impact to Mobile Voice/Data Cells",
       subtitle = "Reported by Return Period, Climate Scenario and Continent.",
       x = "", y = "Direct Damage Cost (USD Billions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Continent')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, 100)) 


path = file.path(folder, 'figures', 'tropical_cyclone_impacts.png')
ggsave(path, units="in", width=8, height=4.5, dpi=300)