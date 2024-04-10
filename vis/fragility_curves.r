## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)
# install.packages("viridis")
library(viridis)

###################
##### 
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'data', 'raw')
setwd(data_directory)

data = read.csv('fragility_curves_booker_et_al.csv')

data$category = factor(data$category,
                    levels=c(
                      "microwave_misalignment",
                      "loss_of_cell_antenna",
                      "loss_of_off_site_power",
                      "loss_of_onsite_power",
                      "structural_failure",
                      "foundation_failure"
                    ),
                    labels=c(
                      "Microwave\nMisalignment",
                      "Loss of\nCell Antenna",
                      "Loss of\nOff-Site Power",
                      "Loss of\nOn-Site Power",
                      "Structural\nFailure",
                      "Foundation\nFailure"
                    )
)

plot = ggplot(data, aes(
  x=speed, y=probability_of_failure, group=category, color=category)) +
  geom_line(aes(linetype=category)) + geom_point(aes(shape=category)) +
  theme(legend.position = 'bottom',
      axis.text.x = element_text(angle=0, hjust=.75, vjust=.5)) +
  labs(title = "Wind Speed Vulnerability Curves",
       subtitle = "Adapted from Booker et al. (2010).",
       x = "Wind Speed (km/hr)",
       y = "Probability of Failure", fill=NULL) +
  scale_x_continuous(expand = c(0, -1), limits=c(0, 81)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, 1)) +
  scale_color_viridis(discrete = TRUE, option = "D", direction=-1) +
  guides(
    color=guide_legend(ncol=5, title='Damage\nType'),
    shape=guide_legend(ncol=5, title='Damage\nType'),
    linetype=guide_legend(ncol=5, title='Damage\nType')
    ) 

dir.create(file.path(folder, 'figures'), showWarnings = FALSE)
path = file.path(folder, 'figures', 'fragility_curve_wind.png')
png(
  path,
  units = "in",
  width = 5.5,
  height = 4,
  res = 480
)
print(plot)
dev.off()