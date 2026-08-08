; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; Accessibility Options System
; Phase 117: Inclusive Features
; -----------------------------------------------------------------------------
; FEATURES:
; - Easy Mode (reduced difficulty)
; - Large Text (50% bigger)
; - Remappable Controls
; - Colorblind Mode (alternative palettes)
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

; Accessibility flags
ACCESSIBILITY_EASY_MODE equ 0
ACCESSIBILITY_LARGE_TEXT equ 1
ACCESSIBILITY_REMAPPED_CONTROLS equ 2
ACCESSIBILITY_COLORBLIND_MODE equ 3

; Colorblind palette types
COLORBLIND_DEUTERANOPIA equ 0  ; Red-green
COLORBLIND_PROTANOPIA equ 1   ; Red-green
COLORBLIND_TRITANOPIA equ 2   ; Blue-yellow

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "Accessibility Variables", WRAM

wAccessibilityFlags:: ds 1  ; Bit field for enabled options
wTextScale:: ds 1            ; 0 = normal, 1 = large
wColorblindType:: ds 1      ; Current colorblind palette type

; Remapped controls
wRemappedButtonA:: ds 1
wRemappedButtonB:: ds 1
wRemappedButtonL:: ds 1
wRemappedButtonR:: ds 1

ENDS

; -----------------------------------------------------------------------------
; Initialize Accessibility Options
; -----------------------------------------------------------------------------

InitAccessibility::
    push af
    
    ; Reset all accessibility options
    xor a
    ld [wAccessibilityFlags], a
    ld [wTextScale], a
    ld [wColorblindType], a
    
    ; Reset remapped controls to defaults
    ld a, BUTTON_A
    ld [wRemappedButtonA], a
    ld a, BUTTON_B
    ld [wRemappedButtonB], a
    ld a, BUTTON_L
    ld [wRemappedButtonL], a
    ld a, BUTTON_R
    ld [wRemappedButtonR], a
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Toggle Easy Mode
; -----------------------------------------------------------------------------

ToggleEasyMode::
    push af
    
    ; Toggle the easy mode flag
    ld a, [wAccessibilityFlags]
    xor (1 << ACCESSIBILITY_EASY_MODE)
    ld [wAccessibilityFlags], a
    
    ; Apply easy mode settings
    call ApplyEasyModeSettings
    
    ; Show confirmation message
    ld hl, EasyModeToggledMessage
    call ShowTextBox
    call PrintText
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Apply Easy Mode Settings
; -----------------------------------------------------------------------------

ApplyEasyModeSettings::
    push af
    
    ; Check if easy mode is enabled
    ld a, [wAccessibilityFlags]
    and (1 << ACCESSIBILITY_EASY_MODE)
    jr z, .disable_easy_mode
    
    ; Enable easy mode
    ld a, 70  ; 70% HP for enemies
    ld [wEnemyHPModifier], a
    ld a, 80  ; 80% ATK for enemies
    ld [wEnemyATKModifier], a
    ld a, 120 ; 120% HP for player
    ld [wPlayerHPModifier], a
    ld a, 110 ; 110% DEF for player
    ld [wPlayerDEFModifier], a
    
    ; Enable one-hit recovery (player doesn't die at 0 HP)
    ld a, 1
    ld [wOneHitRecovery], a
    
    jr .done

.disable_easy_mode:
    ; Disable easy mode
    ld a, 100
    ld [wEnemyHPModifier], a
    ld [wEnemyATKModifier], a
    ld [wPlayerHPModifier], a
    ld [wPlayerDEFModifier], a
    
    ; Disable one-hit recovery
    xor a
    ld [wOneHitRecovery], a

.done:
    pop af
    ret

; -----------------------------------------------------------------------------
; Toggle Large Text
; -----------------------------------------------------------------------------

ToggleLargeText::
    push af
    
    ; Toggle the large text flag
    ld a, [wAccessibilityFlags]
    xor (1 << ACCESSIBILITY_LARGE_TEXT)
    ld [wAccessibilityFlags], a
    
    ; Update text scale
    ld a, [wAccessibilityFlags]
    and (1 << ACCESSIBILITY_LARGE_TEXT)
    jr z, .normal_text
    
    ld a, 1
    jr .set_text_scale

.normal_text:
    xor a

.set_text_scale:
    ld [wTextScale], a
    
    ; Show confirmation message
    ld hl, LargeTextToggledMessage
    call ShowTextBox
    call PrintText
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Toggle Colorblind Mode
; -----------------------------------------------------------------------------

ToggleColorblindMode::
    push af
    
    ; Cycle through colorblind types
    ld a, [wColorblindType]
    inc a
    cp 3
    jr c, .set_type
    xor a

.set_type:
    ld [wColorblindType], a
    
    ; Toggle the colorblind flag
    ld a, [wAccessibilityFlags]
    and (1 << ACCESSIBILITY_COLORBLIND_MODE)
    jr nz, .flag_already_set
    
    ld a, [wAccessibilityFlags]
    or (1 << ACCESSIBILITY_COLORBLIND_MODE)
    ld [wAccessibilityFlags], a

.flag_already_set:
    ; Apply colorblind palette
    call ApplyColorblindPalette
    
    ; Show confirmation message
    ld hl, ColorblindModeToggledMessage
    call ShowTextBox
    call PrintText
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Apply Colorblind Palette
; -----------------------------------------------------------------------------

ApplyColorblindPalette::
    push af
    push bc
    push hl
    
    ; Check if colorblind mode is enabled
    ld a, [wAccessibilityFlags]
    and (1 << ACCESSIBILITY_COLORBLIND_MODE)
    jr z, .done
    
    ; Get the palette type
    ld a, [wColorblindType]
    and a
    jr z, .deuteranopia
    dec a
    jr z, .protanopia
    
    ; Tritanopia
    ld hl, TritanopiaPalette
    jr .apply_palette

.deuteranopia:
    ld hl, DeuteranopiaPalette
    jr .apply_palette

.protanopia:
    ld hl, ProtanopiaPalette

.apply_palette:
    ; Apply palette to PPU
    ; This would copy the palette data to the GBA's palette memory
    call CopyPaletteToPPU

.done:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Remap Controls
; Input: a = button to remap (0=A, 1=B, 2=L, 3=R)
;        b = new button mapping
; -----------------------------------------------------------------------------

RemapControl::
    push af
    push hl
    
    ; Store the new mapping
    cp 0
    jr z, .remap_a
    cp 1
    jr z, .remap_b
    cp 2
    jr z, .remap_l
    cp 3
    jr z, .remap_r
    jr .done

.remap_a:
    ld [wRemappedButtonA], b
    jr .done

.remap_b:
    ld [wRemappedButtonB], b
    jr .done

.remap_l:
    ld [wRemappedButtonL], b
    jr .done

.remap_r:
    ld [wRemappedButtonR], b

.done:
    ; Show confirmation message
    ld hl, ControlsRemappedMessage
    call ShowTextBox
    call PrintText
    
    pop hl
    pop af
    ret

; -----------------------------------------------------------------------------
; Get Remapped Button
; Input: a = original button (BUTTON_A, BUTTON_B, etc.)
; Output: a = remapped button
; -----------------------------------------------------------------------------

GetRemappedButton::
    push bc
    push hl
    
    ; Check if controls are remapped
    ld b, a
    ld a, [wAccessibilityFlags]
    and (1 << ACCESSIBILITY_REMAPPED_CONTROLS)
    jr z, .not_remapped
    
    ; Controls are remapped - look up the mapping
    ld a, b
    cp BUTTON_A
    jr z, .get_a
    cp BUTTON_B
    jr z, .get_b
    cp BUTTON_L
    jr z, .get_l
    cp BUTTON_R
    jr z, .get_r
    
    ; Not a remappable button
    ld a, b
    jr .done

.get_a:
    ld a, [wRemappedButtonA]
    jr .done

.get_b:
    ld a, [wRemappedButtonB]
    jr .done

.get_l:
    ld a, [wRemappedButtonL]
    jr .done

.get_r:
    ld a, [wRemappedButtonR]

.done:
    pop hl
    pop bc
    ret

.not_remapped:
    ; Controls not remapped - return original
    ld a, b
    jr .done

; -----------------------------------------------------------------------------
; Accessibility Options Menu
; -----------------------------------------------------------------------------

AccessibilityMenu::
    db "Accessibility", $00
    db "Easy Mode", $00
    db "Large Text", $00
    db "Colorblind Mode", $00
    db "Remap Controls", $00
    db "Back", $00
    db 0

EasyModeMenu::
    db "Easy Mode", $00
    db "ON", $00
    db "OFF", $00
    db 0

LargeTextMenu::
    db "Large Text", $00
    db "ON", $00
    db "OFF", $00
    db 0

ColorblindMenu::
    db "Colorblind Mode", $00
    db "Deuteranopia", $00
    db "Protanopia", $00
    db "Tritanopia", $00
    db "OFF", $00
    db 0

ControlsMenu::
    db "Remap Controls", $00
    db "Button A", $00
    db "Button B", $00
    db "Button L", $00
    db "Button R", $00
    db "Back", $00
    db 0

ButtonMenu::
    db "Map to:", $00
    db "A", $00
    db "B", $00
    db "L", $00
    db "R", $00
    db "Start", $00
    db "Select", $00
    db 0

; -----------------------------------------------------------------------------
; Show Accessibility Menu
; -----------------------------------------------------------------------------

ShowAccessibilityMenu::
    push af
    push bc
    push hl

    ; Save current menu state
    ld a, [wCurrentMenu]
    push af

.menu_loop:
    ; Display menu
    ld hl, AccessibilityMenu
    call ShowMenu
    jr c, .exit_menu
    
    ; Process selection
    cp 1  ; Easy Mode
    jr z, .show_easy_mode_menu
    cp 2  ; Large Text
    jr z, .show_large_text_menu
    cp 3  ; Colorblind Mode
    jr z, .show_colorblind_menu
    cp 4  ; Remap Controls
    jr z, .show_controls_menu
    cp 5  ; Back
    jr z, .exit_menu
    
    jr .menu_loop

.show_easy_mode_menu:
    ld hl, EasyModeMenu
    call ShowMenu
    jr c, .menu_loop
    
    cp 1  ; ON
    jr z, .enable_easy_mode
    cp 2  ; OFF
    jr z, .disable_easy_mode
    
    jr .show_easy_mode_menu

.enable_easy_mode:
    ld a, [wAccessibilityFlags]
    set ACCESSIBILITY_EASY_MODE, a
    ld [wAccessibilityFlags], a
    call ApplyEasyModeSettings
    jr .menu_loop

.disable_easy_mode:
    ld a, [wAccessibilityFlags]
    res ACCESSIBILITY_EASY_MODE, a
    ld [wAccessibilityFlags], a
    call ApplyEasyModeSettings
    jr .menu_loop

.show_large_text_menu:
    ld hl, LargeTextMenu
    call ShowMenu
    jr c, .menu_loop
    
    cp 1  ; ON
    jr z, .enable_large_text
    cp 2  ; OFF
    jr z, .disable_large_text
    
    jr .show_large_text_menu

.enable_large_text:
    call ToggleLargeText
    jr .menu_loop

.disable_large_text:
    ld a, [wAccessibilityFlags]
    res ACCESSIBILITY_LARGE_TEXT, a
    ld [wAccessibilityFlags], a
    xor a
    ld [wTextScale], a
    jr .menu_loop

.show_colorblind_menu:
    ld hl, ColorblindMenu
    call ShowMenu
    jr c, .menu_loop
    
    cp 1  ; Deuteranopia
    jr z, .set_deuteranopia
    cp 2  ; Protanopia
    jr z, .set_protanopia
    cp 3  ; Tritanopia
    jr z, .set_tritanopia
    cp 4  ; OFF
    jr z, .disable_colorblind
    
    jr .show_colorblind_menu

.set_deuteranopia:
    xor a
    jr .set_colorblind

.set_protanopia:
    ld a, 1
    jr .set_colorblind

.set_tritanopia:
    ld a, 2

.set_colorblind:
    ld [wColorblindType], a
    ld a, [wAccessibilityFlags]
    or (1 << ACCESSIBILITY_COLORBLIND_MODE)
    ld [wAccessibilityFlags], a
    call ApplyColorblindPalette
    jr .menu_loop

.disable_colorblind:
    ld a, [wAccessibilityFlags]
    res ACCESSIBILITY_COLORBLIND_MODE, a
    ld [wAccessibilityFlags], a
    xor a
    ld [wColorblindType], a
    call ApplyColorblindPalette
    jr .menu_loop

.show_controls_menu:
    call ShowControlsMenu
    jr .menu_loop

.exit_menu:
    ; Restore previous menu state
    pop af
    ld [wCurrentMenu], a

    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Show Controls Menu
; -----------------------------------------------------------------------------

ShowControlsMenu::
    push af
    push bc
    push hl

.controls_loop:
    ld hl, ControlsMenu
    call ShowMenu
    jr c, .exit_controls
    
    cp 1  ; Button A
    jr z, .remap_button_a
    cp 2  ; Button B
    jr z, .remap_button_b
    cp 3  ; Button L
    jr z, .remap_button_l
    cp 4  ; Button R
    jr z, .remap_button_r
    cp 5  ; Back
    jr z, .exit_controls
    
    jr .controls_loop

.remap_button_a:
    ld a, 0  ; Remapping button A
    call ShowButtonRemapMenu
    jr .controls_loop

.remap_button_b:
    ld a, 1  ; Remapping button B
    call ShowButtonRemapMenu
    jr .controls_loop

.remap_button_l:
    ld a, 2  ; Remapping button L
    call ShowButtonRemapMenu
    jr .controls_loop

.remap_button_r:
    ld a, 3  ; Remapping button R
    call ShowButtonRemapMenu
    jr .controls_loop

.exit_controls:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Show Button Remap Menu
; Input: a = button to remap (0=A, 1=B, 2=L, 3=R)
; -----------------------------------------------------------------------------

ShowButtonRemapMenu::
    push af
    push bc
    push hl
    
    ; Save button to remap
    ld [wTempButton], a
    
.button_remap_loop:
    ; Display menu
    ld hl, ButtonMenu
    call ShowMenu
    jr c, .exit_button_remap
    
    ; Process selection
    cp 1  ; A
    jr z, .map_to_a
    cp 2  ; B
    jr z, .map_to_b
    cp 3  ; L
    jr z, .map_to_l
    cp 4  ; R
    jr z, .map_to_r
    cp 5  ; Start
    jr z, .map_to_start
    cp 6  ; Select
    jr z, .map_to_select
    
    jr .button_remap_loop

.map_to_a:
    ld b, BUTTON_A
    jr .do_remap

.map_to_b:
    ld b, BUTTON_B
    jr .do_remap

.map_to_l:
    ld b, BUTTON_L
    jr .do_remap

.map_to_r:
    ld b, BUTTON_R
    jr .do_remap

.map_to_start:
    ld b, BUTTON_START
    jr .do_remap

.map_to_select:
    ld b, BUTTON_SELECT

.do_remap:
    ; Remap the button
    ld a, [wTempButton]
    call RemapControl
    
    ; Enable remapped controls flag
    ld a, [wAccessibilityFlags]
    or (1 << ACCESSIBILITY_REMAPPED_CONTROLS)
    ld [wAccessibilityFlags], a
    
    jr .button_remap_loop

.exit_button_remap:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Palette Data for Colorblind Modes
; -----------------------------------------------------------------------------

DeuteranopiaPalette:
    ; Red-green colorblind palette
    ; Original: R, G, B
    ; Modified: Shift red and green to be more distinguishable
    db $00, $00, $00, $00  ; Transparent
    db $00, $1F, $00, $00  ; Dark green -> Dark blue
    db $00, $3F, $00, $00  ; Green -> Blue
    db $1F, $00, $00, $00  ; Dark red -> Dark purple
    db $3F, $00, $00, $00  ; Red -> Purple
    ; ... more colors

ProtanopiaPalette:
    ; Red-green colorblind palette (different adjustment)
    db $00, $00, $00, $00  ; Transparent
    db $00, $1F, $00, $00  ; Dark green -> Dark cyan
    db $00, $3F, $00, $00  ; Green -> Cyan
    db $00, $00, $1F, $00  ; Dark red -> Dark blue
    db $00, $00, $3F, $00  ; Red -> Blue
    ; ... more colors

TritanopiaPalette:
    ; Blue-yellow colorblind palette
    db $00, $00, $00, $00  ; Transparent
    db $1F, $00, $00, $00  ; Dark blue -> Dark red
    db $3F, $00, $00, $00  ; Blue -> Red
    db $00, $00, $1F, $00  ; Dark yellow -> Dark green
    db $00, $00, $3F, $00  ; Yellow -> Green
    ; ... more colors

; -----------------------------------------------------------------------------
; Messages
; -----------------------------------------------------------------------------

EasyModeToggledMessage::
    db "Easy Mode ", $0A
    db "toggled.", $FF

LargeTextToggledMessage::
    db "Large Text ", $0A
    db "toggled.", $FF

ColorblindModeToggledMessage::
    db "Colorblind Mode ", $0A
    db "toggled.", $FF

ControlsRemappedMessage::
    db "Controls ", $0A
    db "remapped.", $FF

; -----------------------------------------------------------------------------
; Temporary Variables
; -----------------------------------------------------------------------------

SECTION "Accessibility Temp Variables", WRAM

wTempButton:: ds 1
wOneHitRecovery:: ds 1
wEnemyHPModifier:: ds 1
wEnemyATKModifier:: ds 1
wPlayerHPModifier:: ds 1
wPlayerDEFModifier:: ds 1

ENDS

; -----------------------------------------------------------------------------
; Save/Load Accessibility Settings
; -----------------------------------------------------------------------------

SaveAccessibilitySettings::
    ; Save to SRAM
    ld a, [wAccessibilityFlags]
    ld [sAccessibilityFlags], a
    ld a, [wTextScale]
    ld [sTextScale], a
    ld a, [wColorblindType]
    ld [sColorblindType], a
    ld a, [wRemappedButtonA]
    ld [sRemappedButtonA], a
    ld a, [wRemappedButtonB]
    ld [sRemappedButtonB], a
    ld a, [wRemappedButtonL]
    ld [sRemappedButtonL], a
    ld a, [wRemappedButtonR]
    ld [sRemappedButtonR], a
    ret

LoadAccessibilitySettings::
    ; Load from SRAM
    ld a, [sAccessibilityFlags]
    ld [wAccessibilityFlags], a
    ld a, [sTextScale]
    ld [wTextScale], a
    ld a, [sColorblindType]
    ld [wColorblindType], a
    ld a, [sRemappedButtonA]
    ld [wRemappedButtonA], a
    ld a, [sRemappedButtonB]
    ld [wRemappedButtonB], a
    ld a, [sRemappedButtonL]
    ld [wRemappedButtonL], a
    ld a, [sRemappedButtonR]
    ld [wRemappedButtonR], a
    ret

; -----------------------------------------------------------------------------
; SRAM Variables
; -----------------------------------------------------------------------------

SECTION "Accessibility SRAM", SRAM

sAccessibilityFlags:: ds 1
sTextScale:: ds 1
sColorblindType:: ds 1
sRemappedButtonA:: ds 1
sRemappedButtonB:: ds 1
sRemappedButtonL:: ds 1
sRemappedButtonR:: ds 1

ENDS
