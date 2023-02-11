// ISO-Designer ISO 11783   Version 5.6.1.5243 Jetter AG
// Do not change!

#define WorkingSet_0_Offset                                     1
#define DataMask_1000_Offset                                   21
#define SoftKeyMask_4000_Offset                                41
#define SoftKeyMask_4001_Offset                                71
#define SoftKey_5000_Offset                                   101
#define SoftKey_5001_Offset                                   114
#define SoftKey_5002_Offset                                   127
#define SoftKey_5003_Offset                                   140
#define SoftKey_5004_Offset                                   153
#define SoftKey_5005_Offset                                   166
#define SoftKey_5006_Offset                                   179
#define SoftKey_5007_Offset                                   192
#define SoftKey_5008_Offset                                   205
#define SoftKey_5009_Offset                                   218
#define SoftKey_5010_Offset                                   231
#define SoftKey_5011_Offset                                   244
#define SoftKey_5012_Offset                                   257
#define SoftKey_5013_Offset                                   264
#define SoftKey_5015_Offset                                   271
#define SoftKey_5016_Offset                                   284
#define SoftKey_5017_Offset                                   297
#define SoftKey_5018_Offset                                   304
#define SoftKey_5019_Offset                                   311
#define SoftKey_5021_Offset                                   318
#define SoftKey_5022_Offset                                   325
#define SoftKey_5023_Offset                                   332
#define Button_6000_Offset                                    339
#define Button_6001_Offset                                    358
#define page_2_MAIN_Offset                                    377
#define page_1_MAIN_Offset                                   1042
#define workingset_pic_Offset                                1707
#define Automatik_ein_Offset                                 2327
#define Automatik_aus_Offset                                 2974
#define Einfuelldom_Offset                                   3621
#define EXACUT_Offset                                        4268
#define Seitenschieber_Offset                                4915
#define Heckschieber_Offset                                  5481
#define zusammenklappen_Offset                               6101
#define auseinanderklappen_Offset                            6748
#define Verteiler_heben_Offset                               7395
#define Verteiler_senken_Offset                              8042
#define Knickdeichsel_heben_Offset                           8689
#define Knickdeichsel_senken_Offset                          9318
#define lightbulb_Offset                                     9947
#define trash_icon_Offset                                   10476
#define page_1_AUX_Offset                                   11141
#define page_2_AUX_Offset                                   11806
#define AuxFunction2_31000_Offset                           12471
#define AuxFunction2_31001_Offset                           12483
#define AuxFunction2_31002_Offset                           12495
#define AuxFunction2_31003_Offset                           12507
#define AuxFunction2_31004_Offset                           12519
#define AuxFunction2_31005_Offset                           12531
#define AuxFunction2_31006_Offset                           12543
#define AuxFunction2_31007_Offset                           12555
#define AuxFunction2_31008_Offset                           12567
#define AuxFunction2_31009_Offset                           12579
#define AuxFunction2_31010_Offset                           12591
#define AuxFunction2_31011_Offset                           12603
#define AuxFunction2_31015_Offset                           12615
#define AuxFunction2_31016_Offset                           12627
#define AuxFunction2_31024_Offset                           12639
#define AuxFunction2_31025_Offset                           12651

#define ISO_OP_MEMORY_CLASS

#define ISO_OP_DefaultPool_Size  12663
extern const unsigned char ISO_OP_MEMORY_CLASS isoOP_DefaultPool[];

#define ISO_OP_DefaultPool_ObjectNumber     63
extern const unsigned long ISO_OP_MEMORY_CLASS isoOP_DefaultPool_Offset[];
extern const unsigned long ISO_OP_MEMORY_CLASS isoOP_DefaultPool_Offset_Id[];
#define ISO_OP_DefaultPool_Scale_Offset      1

#define ID_NULL  0xFFFF

#define TYPEID_WORKSET        0
#define TYPEID_DATAMASK       1
#define TYPEID_ALARMMASK      2
#define TYPEID_CONTAINER      3
#define TYPEID_SKEYMASK       4
#define TYPEID_SOFTKEY        5
#define TYPEID_BUTTON         6
#define TYPEID_INBOOL         7
#define TYPEID_INSTR          8
#define TYPEID_INNUM          9
#define TYPEID_INLIST        10
#define TYPEID_OUTSTR        11
#define TYPEID_OUTNUM        12
#define TYPEID_OUTLINE       13
#define TYPEID_OUTRECT       14
#define TYPEID_OUTELLIPSE    15
#define TYPEID_OUTPOLY       16
#define TYPEID_OUTMETER      17
#define TYPEID_OUTLINBAR     18
#define TYPEID_OUTARCBAR     19
#define TYPEID_OUTPICT       20
#define TYPEID_VARNUM        21
#define TYPEID_VARSTR        22
#define TYPEID_FONTATTR      23
#define TYPEID_LINEATTR      24
#define TYPEID_FILLATTR      25
#define TYPEID_INPATTR       26
#define TYPEID_OBJPTR        27
#define TYPEID_MACRO         28
#define TYPEID_AUXFUNC       29
#define TYPEID_AUXINP        30
#define TYPEID_AUXFUNC2      31
#define TYPEID_AUXINP2       32
#define TYPEID_AUXPTR        33
#define TYPEID_WINMASK       34
#define TYPEID_KEYGROUP      35
#define TYPEID_GRPHCTXT      36
#define TYPEID_OUTLIST       37
#define TYPEID_EXTINPATTR    38
#define TYPEID_COLORMAP      39
#define TYPEID_OBJLBLREF     40
#define TYPEID_EXTOBJDEF     41
#define TYPEID_EXTREFNAME    42
#define TYPEID_EXTOBJPTR     43
#define TYPEID_ANIMATION     44
#define TYPEID_COLORPAL      45
#define TYPEID_GRAPHDATA     46
#define TYPEID_WSSPECIAL     47
#define TYPEID_SCALEGRAPH    48

#define EV_REFRESH            0
#define EV_ACT                1
#define EV_DEACT              2
#define EV_SHOW               3
#define EV_HIDE               4
#define EV_ENABLE             5
#define EV_DISABLE            6
#define EV_CHGACTMASK         7
#define EV_CHGSKEYMASK        8
#define EV_CHGATTR            9
#define EV_CHGBKCOLOR        10
#define EV_CHGFONTATTR       11
#define EV_CHGLINEATTR       12
#define EV_CHGFILLATTR       13
#define EV_CHGCHILDLOC       14
#define EV_CHGSIZE           15
#define EV_CHGVAL            16
#define EV_CHGPRIOR          17
#define EV_CHGENDPNT         18
#define EV_SELINPUT          19
#define EV_DESELINPUT        20
#define EV_ESC               21
#define EV_ENTERVAL          22
#define EV_ENTERCHGVAL       23
#define EV_KEYPRESS          24
#define EV_KEYRELEASE        25
#define EV_CHGCHILDPOS       26

#define CMD_HIDE_SHOW               160
#define CMD_ENABLE_DISABLE          161
#define CMD_SELECT_INPUT_OBJECT     162
#define CMD_CONTROL_AUDIO_DEVICE    163
#define CMD_SET_AUDIO_VOLUME        164
#define CMD_CHANGE_CHILD_LOCATION   165
#define CMD_CHANGE_SIZE             166
#define CMD_CHANGE_BACKGROUND_COLOR 167
#define CMD_CHANGE_NUMERIC_VALUE    168
#define CMD_CHANGE_END_POINT        169
#define CMD_CHANGE_FONT_ATTRIBUTES  170
#define CMD_CHANGE_LINE_ATTRIBUTES  171
#define CMD_CHANGE_FILL_ATTRIBUTES  172
#define CMD_CHANGE_ACTIVE_MASK      173
#define CMD_CHANGE_SOFT_KEY_MASK    174
#define CMD_CHANGE_ATTRIBUTE        175
#define CMD_CHANGE_PRIORITY         176
#define CMD_CHANGE_LIST_ITEM        177
#define CMD_CHANGE_STRING_VALUE     179
#define CMD_CHANGE_CHILD_POSITION   180
#define CMD_SET_OBJECT_LABEL        181
#define CMD_CHANGE_POLYGON_POINT    182
#define CMD_CHANGE_POLYGON_SCALE    183
#define CMD_GRAPHICS_CONTEXT        184
#define CMD_GET_ATTRIBUTE           185
#define CMD_SELECT_COLOURMAP_OR_PALETTE 186
#define CMD_EXECUTE_EXTENDED_MACRO  188
#define CMD_LOCK_UNLOCK_MASK        189
#define CMD_EXECUTE_MACRO           190

#define COLOR_BLACK       0
#define COLOR_WHITE       1
#define COLOR_GREEN       2
#define COLOR_TEAL        3
#define COLOR_MAROON      4
#define COLOR_PURPLE      5
#define COLOR_OLIVE       6
#define COLOR_SILVER      7
#define COLOR_GREY        8
#define COLOR_BLUE        9
#define COLOR_LIME       10
#define COLOR_CYAN       11
#define COLOR_RED        12
#define COLOR_MAGENTA    13
#define COLOR_YELLOW     14
#define COLOR_NAVY       15

#define FLOAT_1      0x00, 0x00, 0x80, 0x3F
#define FLOAT_10     0x00, 0x00, 0x20, 0x41
#define FLOAT_100    0x00, 0x00, 0xC8, 0x42
#define FLOAT_1000   0x00, 0x00, 0x7A, 0x44
#define FLOAT_0_1    0xCD, 0xCC, 0xCC, 0x3D
#define FLOAT_0_01   0x0A, 0xD7, 0x23, 0x3C
#define FLOAT_0_001  0x6F, 0x12, 0x83, 0x3A
