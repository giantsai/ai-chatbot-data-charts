#!/usr/bin/env Rscript

# Retrieve command-line arguments
args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript generate_chart.R <input_file> <output_image>")
}

input_file <- args[1]
output_image <- args[2]

# Load ggplot2 package
library(ggplot2)

# Read the input CSV file
data <- read.csv(input_file)

# Check if required columns exist
if("category" %in% names(data) & "value" %in% names(data)) {
  # Create a bar chart using ggplot2
  p <- ggplot(data, aes(x = category, y = value)) +
    geom_bar(stat = "identity", fill = "steelblue") +
    theme_minimal() +
    ggtitle("R Generated Chart") +
    xlab("Category") +
    ylab("Value")
  
  # Save the plot to the output image file
  ggsave(output_image, plot = p, width = 8, height = 4)
} else {
  # If required columns are missing, output a default plot
  png(output_image, width = 800, height = 400)
  plot(1:10, main = "Data structure not recognized")
  dev.off()
}
