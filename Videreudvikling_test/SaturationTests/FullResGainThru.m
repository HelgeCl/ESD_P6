clc; clear; close all;

% Variables
max_packet_size = 256; % In bits



% --- Load Data ---
Data = readtable('packets_grpNySatTest.csv'); %Ændre navn for at loade ny fil
noReception = linspace(min(Data.gain),0,45);

for i = 1:length(noReception)
    row = array2table([noReception(i) 0 0], 'VariableNames',Data.Properties.VariableNames);
    Data = [row;Data];
end

rssi_db = 20*log10(Data.rssi);

Data.throughput = Data.throughput*max_packet_size;

% --- Plot ---
figure('Name', 'Throughput vs Gain', 'Color', 'w');
ax = axes; hold on; grid on;

yyaxis left
plot(ax, Data.gain, Data.throughput, '-', 'LineWidth', 1.5, 'DisplayName', 'Throughput');
ylabel('Throughput [b/s]');

yyaxis right
plot(ax, Data.gain, rssi_db, '--', 'LineWidth', 1.5, 'DisplayName', 'RSSI (dBm)');
ylabel('RSSI [dBFS]');

% --- Formatting ---
xlabel('Gain [-]');
title('Throughput and RSSI vs Gain');
legend(ax, 'Location', 'northwest');