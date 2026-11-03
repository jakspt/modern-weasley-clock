// stencil for positioning the icons
stencil_outer_diameter = 202; 


stencil_inner_diameter = 152; 


icon_placement_diameter = 182; 

badge_diameter = 20;      


difference() {
    circle(d=stencil_outer_diameter, $fn=200);
    
    circle(d=stencil_inner_diameter, $fn=200);
    
    for (i = [0 : 4]) {
        angle = i * 72;
        
        // Convert the diameter to a radius for the math
        radius = icon_placement_diameter / 2;
        
        pos_x = radius * sin(angle);
        pos_y = radius * cos(angle);
        
        translate([pos_x, pos_y]) {
            //  add 0.5mm tolerance
            circle(d=badge_diameter + 0.5, $fn=60);
        }
    }
}