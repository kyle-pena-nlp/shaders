const int AA = 1;

const float EPS = 1e-8;
const float PI = 3.1415962;


const float RATE_1 = 2. * PI / 10.;
const float RATE_2 = 2. * PI / 1.;
const float PHASE_1 = PI / 2.;
const float LOOP_TIME = 10.;
const float VCR_LOOP_TIME = 5.;

mat2 noise2d_rotator = mat2(-0.8, 0.6, 0.6, 0.8);


// { "loop": ("-1.", 0.01), "blue": ("0.", 0.70), "red": ("1.", 0.10), "green":("2.", 0.10), "purp": ("3.", 0.09) }
#define COLOR_MODE -1.

// { "bloop": ("0", 0.33), "gloop": ("1", 0.33), "scoop": ("2", 0.34) }
#define POLYNOMIAL 0

// { "kalm": ("0.", 0.95), "thunder": ("1.", 0.05) }
#define JITTERY 1.

#define SHAPES 20

const float WILD_B = (POLYNOMIAL == 0) ? 1. : 0.;
const float WILD_C = (POLYNOMIAL == 1) ? 1. : 0.;
const float WILD_D = (POLYNOMIAL == 2) ? 1. : 0.;


const int MAX_ITER = SHAPES;


// Pattern 1
float A() {
    return 1.;
}

float B() {
    return 0.0 + WILD_B * (sin(RATE_1 * iTime));
}

float C() {
    return 0.0 + WILD_C * (-1. + 0.5 * sin(RATE_1 * iTime));//sin(2.*PI*iTime/10.)-1.;
}

float D() {
    return -1.0 + WILD_D * sin(RATE_1 * iTime);
}



float HUE_SHIFT_FRAC() {
    if (COLOR_MODE == -1.) {
        return iTime / 10.;
    }
    else if (COLOR_MODE == 0.) {
        return 0.0;
    }
    else if (COLOR_MODE == 1.) {
        return 0.24;
    }
    else if (COLOR_MODE == 2.) {
        return 0.6;
    }
    else if (COLOR_MODE == 3.) {
        return 0.85;
    }
    else {
        return 0.0;
    }
}



// from https://www.shadertoy.com/view/MsjXRt
// todo: my own implementation
vec3 HueShift (in vec3 Color, in float Shift)
{
    vec3 P = vec3(0.55735)*dot(vec3(0.55735),Color);
    
    vec3 U = Color-P;
    
    vec3 V = cross(vec3(0.55735),U);    

    Color = U*cos(Shift*6.2832) + V*sin(Shift*6.2832) + P;
    
    return Color;
}


struct Z {
    float real;
    float imag;
};

Z add(Z a, Z b, Z c, Z d) {
    return Z(a.real + b.real + c.real + d.real, a.imag + b.imag + c.imag + d.imag);
}

Z add(Z a, Z b, Z c) {
    return Z(a.real + b.real + c.real, a.imag + b.imag + c.imag);
}

Z add(Z a, Z b) {
    return Z(a.real + b.real, a.imag + b.imag);
}

Z power(Z a, int exponent) {
    float r = pow(length(vec2(a.real, a.imag)), float(exponent));
    float cis = float(exponent) * atan(a.imag, a.real);
    return Z(r * cos(cis), r * sin(cis));  
}

Z conj(Z a) {
    return Z(a.real, -a.imag);
}

Z mult(float x, Z z) {
    return Z(x * z.real, x * z.imag);
}

Z mult(Z a, Z b) {
    return Z(a.real * b.real - a.imag * b.imag, a.real * b.imag + a.imag * b.real);
}

Z div(Z a, Z b) {
    
    Z numerator = mult(a, conj(b));
    float denom = mult(b,conj(b)).real;
    denom = denom == 0. ? 1. : denom;
    return mult(1./denom, numerator);
}

struct Poly3 {
    float A;
    float B;
    float C;
    float D;
};



float fx(float x, Poly3 poly) {
    return poly.A*x*x*x + poly.B*x*x + poly.C*x + poly.D;
}

Z fz(Z z, Poly3 poly) {
    return add(mult(poly.A, power(z, 3)), mult(poly.B, power(z, 2)), mult(poly.C, power(z, 1)), Z(poly.D,0.)); 
}


Z dfdx(Z z, Poly3 poly) {
    return add(mult(3.*poly.A, power(z, 2)), mult(2.*poly.B, z), Z(poly.C,0.));
}

// TODO: handle divide by zero without branches or additive smoothing
Z next(Z z, Poly3 poly, Z multiplier) {
    return add(z, mult(multiplier,div(fz(z, poly), dfdx(z, poly))));
}

struct Result {
    int iterations;
    Z zero;
    float success;
    float d;
};

Result newtown_raphson(Z z, Poly3 poly, Z multiplier) {
    for (int i = 0; i < MAX_ITER; i++) {
        float d = z.real*z.real + z.imag*z.imag;
        if (d < EPS) {
            return Result(i, z, 1., d);
        }
        z = next(z, poly, multiplier);
    }
    float d =  z.real*z.real + z.imag*z.imag;
    return Result(MAX_ITER, z, 0., d);
}


void render(out vec4 fragColor, in vec2 fragCoord ) {
    // Normalized pixel coordinates (from 0 to 1)

    // AA accumulation
    vec3 tot = vec3(0.);
    
    // accumulation for finite differences
    // (I'm computing the gradient *while* doing AA)
    float dFdX  = 0.;
    float dFdY  = 0.;

    for (int i = -AA; i <= AA; i++) {
        for (int j = -AA; j <= AA; j++) {

            vec2 uv = ((fragCoord+((1.)/(2.*float(AA)))*vec2(i,j))/iResolution.xx);
            uv -= 0.5 * (iResolution.xy/iResolution.xx);

            Z z = Z(uv.x, uv.y);
            
            Z a = Z(-1.+0.9*sin(RATE_1*iTime),-0.1+0.9*cos(RATE_1*iTime));
            Result result = newtown_raphson(z, Poly3(A(),B(),C(),D()), a);

            float shade = clamp(float(result.iterations) / float(10), 0., 1.);
            
            dFdX += float(i) * shade;
            dFdY += float(j) * shade;

            // Time varying pixel color
            vec3 color = shade * shade * shade * shade * 0.5*(1.+clamp(vec3(result.zero.real, result.zero.imag, 1.), -1., 1.));
            
            tot += 0.15*(HueShift(color, HUE_SHIFT_FRAC()));
        }
    }

    tot /= float(AA * AA);
    
    // central differences is ordinarily by 2.*h_i, but we are in a 3x3 box, so we divide by 6.=2.*3.
    //dFdX *= 10.;
    //dFdY *= 10.;
    
    
    // compute lighting using normal
    //tot *= dot(normalize(vec3(dFdX,dFdY,1.)), LIGHT_DIR());


    // Output to screen
    fragColor = vec4(tot,1.0);
}

// from IQ @ https://www.shadertoy.com/view/XdXGW8
vec2 grad2( ivec2 z )  // replace this anything that returns a random vector
{
    // 2D to 1D  (feel free to replace by some other)
    int n = z.x+z.y*11111;

    // Hugo Elias hash (feel free to replace by another one)
    n = (n<<13)^n;
    n = (n*(n*n*15731+789221)+1376312589)>>16;

    // Perlin style vectors
    n &= 7;
    vec2 gr = vec2(n&1,n>>1)*2.0-1.0;
    return ( n>=6 ) ? vec2(0.0,gr.x) : 
           ( n>=4 ) ? vec2(gr.x,0.0) :
                              gr;                             
}

float noise2_octave(in vec2 p, float intensity) 
{
     ivec2 i = ivec2(floor( p ));
     vec2 f =       fract( p );
	
	vec2 u = f*f*(3.0-2.0*f); // feel free to replace by a quintic smoothstep instead

    return mix( mix( dot( intensity*grad2( i+ivec2(0,0) ), f-vec2(0.0,0.0) ), 
                     dot( intensity*grad2( i+ivec2(1,0) ), f-vec2(1.0,0.0) ), u.x),
                mix( dot( intensity*grad2( i+ivec2(0,1) ), f-vec2(0.0,1.0) ), 
                     dot( intensity*grad2( i+ivec2(1,1) ), f-vec2(1.0,1.0) ), u.x), u.y);
}


// from IQ @ https://www.shadertoy.com/view/XdXGW8
float noise2( in vec2 p, int octaves, float intensity )
{
    float f = 0.;
    for (int i = 0; i < octaves; i++) {
        float coef = pow(2., -float(i + 1));
        f += coef*noise2_octave(p,intensity); 
        p = p*noise2d_rotator*2.01;
    }
    //f = 0.5 + 0.5*f;
    return f;
}

float fbm2( in vec2 x, int octaves, in float H )
{    
    float G = exp2(-H);
    float f = 1.0;
    float a = 1.0;
    float t = 0.0;
    for( int i=0; i<octaves; i++ )
    {
        t += a*noise2(f*x, 1, 1.);
        f *= 2.01;
        a *= G;
    }
    return t;
}

// https://www.iquilezles.org/www/articles/warp/warp.htm
vec2 distort2(in vec2 u, int iters, float scale, float intensity, float time) {
    vec2 p = vec2(u);
    p = vec2(
            fbm2(u+vec2(0.0,0.0),1,1.),
            fbm2(u+vec2(5.2,1.3),1,1.));
    for (int i = 0; i < iters-1; i++) 
    {
        p = vec2(
            fbm2(u + scale*p+vec2(1.7,9.2),1,1.),
            fbm2(u + scale*p+vec2(8.3,2.8),1,1.));
            
        p += vec2(time);
    }
    return u+intensity*p;
}

vec2 getJitter(float iTime)
{
    return 0.3*(distort2(vec2(iTime), 5, 1., 1., 0.) - vec2(iTime)); 
}

vec2 jitter(in vec2 fragCoord, float time) {
    vec2 jitter1 = getJitter(mod(iTime,LOOP_TIME));
    vec2 jitter2 =  getJitter(mod(iTime,LOOP_TIME) - LOOP_TIME);  
    vec2 jitter = mix(jitter1, jitter2, mod(iTime/LOOP_TIME,1.));
    return 1000.*jitter;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 jitter_amt = jitter(fragCoord, iTime);
    fragCoord += JITTERY * jitter_amt;
    

    render(fragColor, fragCoord);
    
    
    if (JITTERY == 1.) {
        float fade = 10./length(jitter_amt);
        fragColor = fade * fragColor;
    }
    
    


}