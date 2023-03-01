## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

###################
##### Coastal flooding
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'validation')
setwd(data_directory)

data = read_csv('cell_count_regional.csv')

sum(data$cells_3g,data$cells_4g,data$cells_5g)

data = select(data, iso3, cells_2g, cells_3g, cells_4g, cells_5g)

data = data %>% 
  pivot_longer(!iso3, names_to = "radio", values_to = "count")

data = data %>%
  group_by(iso3, radio) %>%
  summarize(
    count = sum(count)
  )

country_info = read_csv(file.path(folder, '..', 'data','raw', 'countries.csv'))
country_info = select(country_info, iso3, continent, flood_region)
all_data = merge(data, country_info,by="iso3")

data = all_data %>%
  group_by(continent, radio) %>%
  summarize(
    count = round(sum(count)/1e6,2)
  )



data$radio = factor(data$radio,
                            levels=c(
                              "cells_2g",
                              "cells_3g",
                              "cells_4g",
                              "cells_5g"
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

max_y_value = max(data$count, na.rm=TRUE)

plot1 = 
  ggplot(data, 
       aes(x=continent, y=count, fill=radio)) + 
  # coord_flip() + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,1),"")), size = 1.8,
            position = position_dodge(.9), vjust =.5, hjust=-.2, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5)) +
  labs(colour=NULL,
       title = "Quantity of Mobile Voice/Data Cells by Continent and Cellular Generation",
       subtitle = "Data extracted from OpenCelliD on December 24th 2022.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+2))

data = all_data %>%
    group_by(flood_region, radio) %>%
    summarize(
      count = round(sum(count)/1e6,2)
    )

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
                             "CAC", #Central America\n& Caribbean
                             "China",
                             "Japan & Korea",
                             "MENA", #"Middle East\n& North Africa",
                             "N. America", #"North\nAmerica",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "S. America", #"South\nAmerica",
                             "S. Asia", #"South\nAsia",
                             "SE. Asia", #"Southeast\nAsia",
                             "SSA", #"Sub-Saharan\nAfrica",
                             "W. Europe" #"Western\nEurope"
                           )
)

max_y_value = max(data$count, na.rm=TRUE)

plot2 = 
  ggplot(data, 
               aes(x=flood_region, y=count, fill=radio)) + 
  # coord_flip() + 
  geom_bar(stat="identity", position = position_dodge()) +
  geom_text(aes(label = paste(round(count,1),"")), size = 1.8,
            position = position_dodge(1), vjust =.5, hjust=-.3, angle = 90) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5)) +
  labs(colour=NULL,
       title = "Quantity of Mobile Voice/Data Cells by Flood Region and Cellular Generation",
       subtitle = "Data extracted from OpenCelliD on December 24th 2022.",
       x = NULL,
       y = "Cell Count (Millions)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) +
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=5, title='Cell Type')) +
  scale_fill_viridis_d(direction=1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+2))


ggarrange(
  plot1, 
  plot2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'cell_counts.png')
ggsave(path, units="in", width=8, height=7, dpi=300)