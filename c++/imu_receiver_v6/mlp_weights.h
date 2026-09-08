// mlp_weights.h
#ifndef MLP_WEIGHTS_H
#define MLP_WEIGHTS_H

// ============================================================================
// ESTRUCTURAS Y CONSTANTES DEL PERCEPTRON MULTICAPA
// ============================================================================

typedef struct {
    double SumEG[3];
    double SumEA[3];
    double NS;
} Attb;

typedef struct {
    double MinEG[3];
    double MaxEG[3];
    double MinEA[3];
    double MaxEA[3];
    double MinNS;
    double MaxNS;
} MinMax;

const MinMax r = {
    {1121, 102463, 2398},      // MinEG
    {882866, 1737554, 423835}, // MaxEG
    {0.03, 23.99, 0.13},       // MinEA
    {112.77, 279.07, 56.48},   // MaxEA
    32.0,                      // MinNS
    302.0                      // MaxNS
};

const double Ems2_to_Eg = 1.0 / (9.80665 * 9.80665);

// bien_realizado - Node 0, mal_realizado - Node 1: Threshold, n2, n3, n4, n5
const double n0[5] = {-4.6128596494187395, 7.271962069696998, 9.391451037779122, -13.609032353445063, -15.442785307567272};
const double n1[5] = {4.6128596494187395, -7.271962069696998, -9.391451037779122, 13.609032353445063, 15.442785307567272};

// PESOS - NODES
const double n02_Th = -4.044551371029093;
const double n02_EG[3] = {-1.9533412516657682, 2.1117797732832364, 3.7008738089473177};
const double n02_EA[3] = {-4.05613984365648, -9.417971488447751, -0.22316064148245005};
const double n02_NS = 17.39799805351816;

const double n03_Th = -10.648564467740147;
const double n03_EG[3] = {-3.029163894460441, 11.538919737723264, 7.246293988389006};
const double n03_EA[3] = {-13.618617921939457, -2.711086966758214, -11.505836577972191};
const double n03_NS = 13.127867959396218;

const double n04_Th = 7.7168417583773765;
const double n04_EG[3] = {-5.558649228752904, 12.61148100606476, 6.910973683412792};
const double n04_EA[3] = {9.284871254321937, -2.9550209742199423, -5.512144389008965};
const double n04_NS = 0.454554356133417;

const double n05_Th = 7.715367362971807;
const double n05_EG[3] = {4.568097192057056, 11.140464063583996, -10.895180368580245};
const double n05_EA[3] = {7.02440611674875, -1.1960592176519014, 5.185917103657688};
const double n05_NS = 7.081514573276;

#endif // MLP_WEIGHTS_H