 
module location_badge(svg_filename, base_diameter=20, base_thickness=1.5, icon_thickness=1.0, icon_scale=0.05) {
    union() {
        color("Beige") {
        cylinder(h=1.0, d=base_diameter, $fn=60);
        
        translate([0, 0, 1.0]) {
            cylinder(h=0.5, d1=base_diameter, d2=base_diameter-1.0, $fn=60);
        }
        }
        
        color("Black") {
        // Extruded and scaled SVG
        translate([0, 0, base_thickness]) {
            linear_extrude(height = icon_thickness) {
                scale([icon_scale, icon_scale]) {
                    import(svg_filename, center=true); 
                }
            }
        }
    }
}
}


icon_radius = 91; // Half of the 182mm diameter


icons = [
    "icons/leisure.svg",    // Position 0: 0° (Top / 12 o'clock) -> matches LEDs 24-35
    "icons/transit.svg",    // Position 1: 72° (Top Right) -> matches LEDs 36-47
    "icons/peril.svg",      // Position 2: 144° (Bottom Right) -> matches LEDs 48-59
    "icons/home.svg",       // Position 3: 216° (Bottom Left) -> matches LEDs 0-11
    "icons/work.svg"        // Position 4: 288° (Top Left) -> matches LEDs 12-23
];


for (i = [0 : 4]) {
    // Calculate the angle
    angle = i * 72;
    
    // This keeps the icons perfectly upright instead of rotating them upside down
    pos_x = icon_radius * sin(angle);
    pos_y = icon_radius * cos(angle);
    
    translate([pos_x, pos_y, 7.5]) {
        location_badge(icons[i]);
    }
}
