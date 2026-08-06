/*
 * DBZ_Buus_Fury_Hack - small libgba Mode 4 gallery
 *
 * This is a standalone GBA homebrew/demo target. It does not patch or embed a
 * commercial ROM. The generated scene in include/generated_scene.h is just a
 * test asset so the video path can be verified in mGBA before a real ROM-hack
 * insertion pipeline is added.
 */
#include <gba.h>

#include "generated_scene.h"

#define SCREEN_WIDTH        240
#define SCREEN_HEIGHT       160
#define FRAME_BYTES         (SCREEN_WIDTH * SCREEN_HEIGHT)
#define MODE4_FRONT_BUFFER  ((u8 *)0x06000000)
#define MODE4_BACK_BUFFER   ((u8 *)0x0600A000)

#define ROSTER_COUNT 6

typedef enum DemoScreen {
    SCREEN_ROSTER = 0,
    SCREEN_HELP   = 1
} DemoScreen;

static u8 *back_buffer = MODE4_BACK_BUFFER;
static DemoScreen demo_screen = SCREEN_ROSTER;
static u8 selected = 0;
static u32 frame_counter = 0;

static const char *const roster_names[ROSTER_COUNT] = {
    "GOKU SSJ4",
    "TRUNKS DBS",
    "GOKU",
    "BEERUS",
    "HIT",
    "RILDO GT"
};

/* A compact 5x7 font. It intentionally contains only ASCII characters so it
 * can be kept in ROM without a text engine or a tile font conversion step. */
static const char font_chars[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:-/!?().+";

static const u8 font_data[][7] = {
    /* A */ {0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},
    /* B */ {0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E},
    /* C */ {0x0F, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0F},
    /* D */ {0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E},
    /* E */ {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F},
    /* F */ {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10},
    /* G */ {0x0F, 0x10, 0x10, 0x17, 0x11, 0x11, 0x0F},
    /* H */ {0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},
    /* I */ {0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F},
    /* J */ {0x01, 0x01, 0x01, 0x01, 0x11, 0x11, 0x0E},
    /* K */ {0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11},
    /* L */ {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F},
    /* M */ {0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11},
    /* N */ {0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11},
    /* O */ {0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E},
    /* P */ {0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10},
    /* Q */ {0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D},
    /* R */ {0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11},
    /* S */ {0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E},
    /* T */ {0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04},
    /* U */ {0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E},
    /* V */ {0x11, 0x11, 0x11, 0x11, 0x0A, 0x0A, 0x04},
    /* W */ {0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11},
    /* X */ {0x11, 0x0A, 0x0A, 0x04, 0x0A, 0x0A, 0x11},
    /* Y */ {0x11, 0x0A, 0x0A, 0x04, 0x04, 0x04, 0x04},
    /* Z */ {0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},
    /* 0 */ {0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E},
    /* 1 */ {0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E},
    /* 2 */ {0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F},
    /* 3 */ {0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E},
    /* 4 */ {0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02},
    /* 5 */ {0x1F, 0x10, 0x10, 0x1E, 0x01, 0x01, 0x1E},
    /* 6 */ {0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E},
    /* 7 */ {0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},
    /* 8 */ {0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E},
    /* 9 */ {0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E},
    /* : */ {0x00, 0x04, 0x04, 0x00, 0x04, 0x04, 0x00},
    /* - */ {0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00},
    /* / */ {0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10},
    /* ! */ {0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04},
    /* ? */ {0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04},
    /* ( */ {0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02},
    /* ) */ {0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08},
    /* . */ {0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x06},
    /* + */ {0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00}
};

static void put_pixel(u8 *buffer, int x, int y, u8 color)
{
    if ((unsigned)x < SCREEN_WIDTH && (unsigned)y < SCREEN_HEIGHT) {
        buffer[y * SCREEN_WIDTH + x] = color;
    }
}

static void fill_rect(u8 *buffer, int x, int y, int width, int height, u8 color)
{
    int yy;
    int xx;

    for (yy = y; yy < y + height; ++yy) {
        for (xx = x; xx < x + width; ++xx) {
            put_pixel(buffer, xx, yy, color);
        }
    }
}

static void draw_frame(u8 *buffer, int x, int y, int width, int height, u8 color)
{
    fill_rect(buffer, x, y, width, 1, color);
    fill_rect(buffer, x, y + height - 1, width, 1, color);
    fill_rect(buffer, x, y, 1, height, color);
    fill_rect(buffer, x + width - 1, y, 1, height, color);
}

static const u8 *find_glyph(char character)
{
    unsigned int i;

    if (character == ' ') {
        return 0;
    }

    for (i = 0; font_chars[i] != '\0'; ++i) {
        if (font_chars[i] == character) {
            return font_data[i];
        }
    }

    /* The question-mark glyph is the 40th item (26 letters + 10 digits + ':',
     * '-', '/', '!'). */
    return font_data[40];
}

static int draw_char(u8 *buffer, int x, int y, char character, u8 color, int scale)
{
    const u8 *glyph = find_glyph(character);
    int row;
    int column;

    if (character == ' ') {
        return 6 * scale;
    }

    for (row = 0; row < 7; ++row) {
        for (column = 0; column < 5; ++column) {
            if (glyph[row] & (1 << (4 - column))) {
                fill_rect(buffer, x + column * scale, y + row * scale,
                          scale, scale, color);
            }
        }
    }

    return 6 * scale;
}

static void draw_text(u8 *buffer, int x, int y, const char *text, u8 color, int scale)
{
    while (*text != '\0') {
        x += draw_char(buffer, x, y, *text, color, scale);
        ++text;
    }
}

static void draw_shadow_text(u8 *buffer, int x, int y, const char *text,
                             u8 color, int scale)
{
    draw_text(buffer, x + scale, y + scale, text, SCENE_COL_BLACK, scale);
    draw_text(buffer, x, y, text, color, scale);
}

static void load_palette(void)
{
    unsigned int i;

    for (i = 0; i < 256; ++i) {
        BG_PALETTE[i] = generated_scene_palette[i];
    }
}

static void draw_roster(u8 *buffer)
{
    static const int card_x[ROSTER_COUNT] = {4, 82, 160, 4, 82, 160};
    static const int card_y[ROSTER_COUNT] = {26, 26, 26, 88, 88, 88};
    int pulse_color = ((frame_counter >> 4) & 1) ? SCENE_COL_YELLOW : SCENE_COL_CYAN;
    int i;

    dmaCopy(generated_scene_bitmap, buffer, FRAME_BYTES);

    fill_rect(buffer, 0, 0, SCREEN_WIDTH, 22, SCENE_COL_NAVY);
    draw_shadow_text(buffer, 7, 3, "DBZ BUUS FURY", SCENE_COL_YELLOW, 2);
    draw_text(buffer, 8, 17, "GT / SUPER LAB", SCENE_COL_WHITE, 1);

    for (i = 0; i < ROSTER_COUNT; ++i) {
        u8 color = (i == selected) ? pulse_color : SCENE_COL_WHITE;
        draw_frame(buffer, card_x[i] - 2, card_y[i] - 2, 74, 56, color);
    }

    fill_rect(buffer, 0, 146, SCREEN_WIDTH, 14, SCENE_COL_NAVY);
    draw_text(buffer, 5, 149, "A/LEFT/RIGHT: SELECT", SCENE_COL_WHITE, 1);
    draw_text(buffer, 157, 149, "START: INFO", SCENE_COL_CYAN, 1);

    draw_text(buffer, 7, 137, "SELECTED:", SCENE_COL_YELLOW, 1);
    draw_text(buffer, 65, 137, roster_names[selected], SCENE_COL_WHITE, 1);

    /* A tiny animated indicator makes it easy to see that frames are being
     * presented continuously and that the VBlank wait is not blocking input. */
    if ((frame_counter & 0x10) != 0) {
        fill_rect(buffer, 225, 137, 9, 5, SCENE_COL_GREEN);
    } else {
        fill_rect(buffer, 225, 137, 9, 5, SCENE_COL_CYAN);
    }
}

static void draw_help(u8 *buffer)
{
    fill_rect(buffer, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, SCENE_COL_NAVY);
    draw_shadow_text(buffer, 17, 10, "LIBGBA MODE 4", SCENE_COL_YELLOW, 2);
    draw_text(buffer, 25, 37, "VIDEO: 240 X 160 / 8 BIT", SCENE_COL_WHITE, 1);
    draw_text(buffer, 25, 51, "IRQ: VBLANK ENABLED", SCENE_COL_GREEN, 1);
    draw_text(buffer, 25, 65, "BUFFER: DOUBLE BUFFER", SCENE_COL_CYAN, 1);
    draw_text(buffer, 25, 86, "A / B: ROSTER", SCENE_COL_WHITE, 1);
    draw_text(buffer, 25, 100, "START: CHANGE SCREEN", SCENE_COL_WHITE, 1);
    draw_text(buffer, 25, 114, "ESCENA DE PRUEBA PARA MGBA", SCENE_COL_YELLOW, 1);
    draw_frame(buffer, 15, 30, 210, 100, SCENE_COL_PURPLE);
    draw_text(buffer, 57, 143, "B: BACK", SCENE_COL_CYAN, 1);
}

static void render(u8 *buffer)
{
    if (demo_screen == SCREEN_HELP) {
        draw_help(buffer);
    } else {
        draw_roster(buffer);
    }
}

static void handle_input(void)
{
    u16 pressed = keysDown();

    if (pressed & KEY_START) {
        demo_screen = (demo_screen == SCREEN_ROSTER) ? SCREEN_HELP : SCREEN_ROSTER;
    }

    if (demo_screen == SCREEN_HELP) {
        if (pressed & KEY_B) {
            demo_screen = SCREEN_ROSTER;
        }
        return;
    }

    if (pressed & (KEY_A | KEY_RIGHT)) {
        selected = (selected + 1) % ROSTER_COUNT;
    }
    if (pressed & (KEY_LEFT | KEY_B)) {
        selected = (selected == 0) ? (ROSTER_COUNT - 1) : (selected - 1);
    }
}

int main(void)
{
    irqInit();
    irqEnable(IRQ_VBLANK);

    /* Mode 4 uses BG2 and two 240x160 8-bit framebuffers. The visible buffer
     * starts at 0x06000000; the alternate buffer starts at 0x0600A000. */
    SetMode(MODE_4 | BG2_ENABLE);
    load_palette();

    while (1) {
        scanKeys();
        handle_input();
        render(back_buffer);

        /* Present only at VBlank. Rendering happens on the hidden buffer, then
         * the display bit is toggled so mGBA never sees a half-drawn frame. */
        VBlankIntrWait();
        REG_DISPCNT ^= BACKBUFFER;
        back_buffer = (back_buffer == MODE4_BACK_BUFFER)
                    ? MODE4_FRONT_BUFFER
                    : MODE4_BACK_BUFFER;
        ++frame_counter;
    }

    return 0;
}
