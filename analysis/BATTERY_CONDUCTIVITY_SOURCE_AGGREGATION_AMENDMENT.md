# Battery Conductivity Source-Aggregation Amendment

Frozen after the corrected numeric release and before any source model was
fit.

The literature-mined release can contain several accepted values for the same
property, material, and publication. Source-property models therefore use one
median value per `(property, DOI, material)` group. The recipient uses one
median capacity per `(DOI, material, current, cycle, Type, Specifier, Tag,
Info)` group. Frequency and the number of extracted mentions are not used as
weights.

This aggregation is fixed for conductivity and for the voltage and energy
control cards. It cannot be changed by property or after source skill is
observed. Target values are not supplied to source-card construction.

