





void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    fragColor = texture(iChannel2, fragCoord / iResolution.xy);
 }