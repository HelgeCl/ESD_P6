clc; clear; close all;

% --- Load Data ---
Data   = readtable('packets_grpNySatTest.csv');
noReception = linspace(45,0,45);

for i = 1:length(noReception)
    row = array2table([noReception(i) 0], 'VariableNames',Data.Properties.VariableNames);
    Data = [row;Data];
end

Data.throughput = Data.throughput*80;

% --- Plot ---
figure('Name', 'Throughput vs Gain', 'Color', 'w');
ax = axes; hold on; grid on;

plot(ax, Data.gain,   Data.throughput,   '-', 'LineWidth', 1.5, 'DisplayName', 'Mid Word');

% --- Formatting ---
xlabel('Gain [-]');
ylabel('Throughput [b/s]');
title('Throughput vs Gain');
legend(ax, 'Location', 'northwest');