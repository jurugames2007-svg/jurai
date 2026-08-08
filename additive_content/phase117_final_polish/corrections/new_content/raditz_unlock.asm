; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; Secret Character: Raditz Unlock System
; Phase 117: Hidden Content
; -----------------------------------------------------------------------------
; UNLOCK CONDITION: Defeat all DLC bosses without dying
; -----------------------------------------------------------------------------
; Bosses to defeat:
; 1. Broly (LSSJ)
; 2. Meta-Cooler
; 3. Janemba (Second Form)
; 4. Hirudegarn (Adult Form)
; 5. Super 17
; 6. Nova Shenron
; 7. Eis Shenron
; 8. Nuova Shenron
; 9. Haze Shenron
; 10. Bio-Broly
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

NUM_DLC_BOSSES equ 10
RADITZ_UNLOCKED_FLAG equ 5  ; Bit 5 in wUnlockedCharacters

; Boss IDs (must match enemy IDs in game)
BOSS_BROLY_LSSJ equ 200
BOSS_META_COOLER equ 201
BOSS_JANEMBA_2 equ 202
BOSS_HIRUDEGARN_ADULT equ 203
BOSS_SUPER_17 equ 204
BOSS_NOVA_SHENRON equ 205
BOSS_EIS_SHENRON equ 206
BOSS_NUOVA_SHENRON equ 207
BOSS_HAZE_SHENRON equ 208
BOSS_BIO_BROLY equ 209

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "Raditz Unlock Variables", WRAM

wBossesDefeatedNoDeath:: ds 1  ; Bit field: 1 bit per boss, set when defeated without dying
wRaditzUnlockProgress:: ds 1  ; Number of bosses defeated (0-10)
wRaditzUnlocked:: ds 1        ; Flag: 1 if Raditz is unlocked

ENDS

; -----------------------------------------------------------------------------
; Initialize Raditz Unlock System
; -----------------------------------------------------------------------------

InitRaditzUnlock::
    push af
    
    ; Reset all variables
    xor a
    ld [wBossesDefeatedNoDeath], a
    ld [wRaditzUnlockProgress], a
    ld [wRaditzUnlocked], a
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Check Boss Defeat
; Called when a boss is defeated
; Input: a = boss ID
; -----------------------------------------------------------------------------

CheckBossDefeat::
    push af
    push bc
    push hl
    
    ; Check if this is a DLC boss
    cp BOSS_BROLY_LSSJ
    jr z, .is_dlc_boss
    cp BOSS_META_COOLER
    jr z, .is_dlc_boss
    cp BOSS_JANEMBA_2
    jr z, .is_dlc_boss
    cp BOSS_HIRUDEGARN_ADULT
    jr z, .is_dlc_boss
    cp BOSS_SUPER_17
    jr z, .is_dlc_boss
    cp BOSS_NOVA_SHENRON
    jr z, .is_dlc_boss
    cp BOSS_EIS_SHENRON
    jr z, .is_dlc_boss
    cp BOSS_NUOVA_SHENRON
    jr z, .is_dlc_boss
    cp BOSS_HAZE_SHENRON
    jr z, .is_dlc_boss
    cp BOSS_BIO_BROLY
    jr z, .is_dlc_boss
    
    ; Not a DLC boss, exit
    jr .not_dlc_boss

.is_dlc_boss:
    ; Check if player died during this battle
    ld a, [wPlayerDiedInBattle]
    and a
    jr nz, .player_died
    
    ; Player didn't die - mark boss as defeated
    call MarkBossAsDefeated
    
    ; Check if all bosses are defeated
    call CheckAllBossesDefeated
    
.player_died:
.not_dlc_boss:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Mark Boss As Defeated
; Input: a = boss ID
; -----------------------------------------------------------------------------

MarkBossAsDefeated::
    push af
    push bc
    push hl
    
    ; Determine which bit to set based on boss ID
    cp BOSS_BROLY_LSSJ
    jr z, .set_bit_0
    cp BOSS_META_COOLER
    jr z, .set_bit_1
    cp BOSS_JANEMBA_2
    jr z, .set_bit_2
    cp BOSS_HIRUDEGARN_ADULT
    jr z, .set_bit_3
    cp BOSS_SUPER_17
    jr z, .set_bit_4
    cp BOSS_NOVA_SHENRON
    jr z, .set_bit_5
    cp BOSS_EIS_SHENRON
    jr z, .set_bit_6
    cp BOSS_NUOVA_SHENRON
    jr z, .set_bit_7
    cp BOSS_HAZE_SHENRON
    jr z, .set_bit_8
    cp BOSS_BIO_BROLY
    jr z, .set_bit_9
    
    ; Unknown boss, exit
    jr .done

.set_bit_0:
    ld b, 0
    jr .set_bit
.set_bit_1:
    ld b, 1
    jr .set_bit
.set_bit_2:
    ld b, 2
    jr .set_bit
.set_bit_3:
    ld b, 3
    jr .set_bit
.set_bit_4:
    ld b, 4
    jr .set_bit
.set_bit_5:
    ld b, 5
    jr .set_bit
.set_bit_6:
    ld b, 6
    jr .set_bit
.set_bit_7:
    ld b, 7
    jr .set_bit
.set_bit_8:
    ld b, 8
    jr .set_bit
.set_bit_9:
    ld b, 9

.set_bit:
    ; Set the bit for this boss
    ld a, [wBossesDefeatedNoDeath]
    or (1 << b)
    ld [wBossesDefeatedNoDeath], a
    
    ; Increment progress counter
    ld a, [wRaditzUnlockProgress]
    inc a
    ld [wRaditzUnlockProgress], a

.done:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Check All Bosses Defeated
; -----------------------------------------------------------------------------

CheckAllBossesDefeated::
    push af
    push hl
    
    ; Check if all 10 bits are set
    ld a, [wBossesDefeatedNoDeath]
    cp %1111111111  ; All 10 bits set
    jr nz, .not_all_defeated
    
    ; All bosses defeated without dying - unlock Raditz!
    ld a, 1
    ld [wRaditzUnlocked], a
    
    ; Set Raditz as unlocked in character select
    ld a, [wUnlockedCharacters]
    set RADITZ_UNLOCKED_FLAG, a
    ld [wUnlockedCharacters], a
    
    ; Show unlock message
    ld hl, RaditzUnlockedMessage
    call ShowTextBox
    call PrintText
    
    ; Play unlock fanfare
    ld a, SOUND_FANFARE_UNLOCK
    call PlaySound
    
.not_all_defeated:
    pop hl
    pop af
    ret

; -----------------------------------------------------------------------------
; Raditz Unlocked Message
; -----------------------------------------------------------------------------

RaditzUnlockedMessage::
    db "All DLC bosses", $0A
    db "defeated without", $0A
    db "dying!", $0A
    db "", $0A
    db "Raditz has been", $0A
    db "unlocked as a", $0A
    db "playable character!", $FF

; -----------------------------------------------------------------------------
; Check If Raditz Is Unlocked
; Output: carry set if unlocked
; -----------------------------------------------------------------------------

IsRaditzUnlocked::
    push af
    
    ld a, [wRaditzUnlocked]
    and a
    jr z, .not_unlocked
    
    scf
    jr .done

.not_unlocked:
    or a

.done:
    pop af
    ret

; -----------------------------------------------------------------------------
; Get Raditz Stats (when selected as playable character)
; -----------------------------------------------------------------------------

GetRaditzStats::
    ; Return pointer to Raditz's stats
    ld hl, CharacterRaditzStats
    ret

; -----------------------------------------------------------------------------
; Raditz Character Stats
; -----------------------------------------------------------------------------

CharacterRaditzStats:
    db "Raditz", 0
    dw SPRITE_RADITZ
    db CLASS_WARRIOR
    db ALIGNMENT_HERO
    
    ; Base Stats
    db LEVEL_45
    dw HP_2800
    dw ATK_230
    dw DEF_170
    dw SPD_140
    
    ; Growth Rates
    db HP_GROWTH_7
    db ATK_GROWTH_8
    db DEF_GROWTH_7
    db SPD_GROWTH_6
    
    ; Abilities
    db ABILITY_DOUBLE_BUSTER | ABILITY_SAIYAN_RAGE | ABILITY_FINAL_CANNON | ABILITY_AFTERIMAGE
    
    ; Special Flags
    db FLAG_CAN_TRANSFORM | FLAG_SAIYAN
    
    ; Transformation
    db TRANSFORMATION_SUPER_SAIYAN
    dw SSJ_TIMER_0  ; No time limit for standard SSJ
    
    ; End Marker
    db 0

; -----------------------------------------------------------------------------
; Hook into Boss Defeat Event
; -----------------------------------------------------------------------------

; This hook should be called whenever a boss is defeated
BossDefeatHook::
    push af
    
    ; Check if this is a DLC boss
    call CheckBossDefeat
    
    ; Call original boss defeat handler
    call OriginalBossDefeatHandler
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Hook into Character Select Screen
; -----------------------------------------------------------------------------

; This hook adds Raditz to the character select screen if unlocked
CharacterSelectHook::
    push af
    push bc
    push hl
    
    ; Check if Raditz is unlocked
    call IsRaditzUnlocked
    jr nc, .not_unlocked
    
    ; Add Raditz to the character list
    ld hl, CharacterSelectList
    ld bc, CHARACTER_ENTRY_SIZE
    
.find_end:
    ld a, [hl]
    cp 255
    jr z, .found_end
    add hl, bc
    jr .find_end
    
.found_end:
    ; Add Raditz entry
    ld a, CHARACTER_RADITZ
    ld [hli], a
    ld a, <RaditzSelectSprite
    ld [hli], a
    ld a, >RaditzSelectSprite
    ld [hli], a
    ld a, PAL_RADITZ
    ld [hl], a
    
.not_unlocked:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Save/Load Raditz Unlock Status
; -----------------------------------------------------------------------------

SaveRaditzUnlockStatus::
    ; Save to SRAM
    ld a, [wBossesDefeatedNoDeath]
    ld [sBossesDefeatedNoDeath], a
    ld a, [wRaditzUnlockProgress]
    ld [sRaditzUnlockProgress], a
    ld a, [wRaditzUnlocked]
    ld [sRaditzUnlocked], a
    ret

LoadRaditzUnlockStatus::
    ; Load from SRAM
    ld a, [sBossesDefeatedNoDeath]
    ld [wBossesDefeatedNoDeath], a
    ld a, [sRaditzUnlockProgress]
    ld [wRaditzUnlockProgress], a
    ld a, [sRaditzUnlocked]
    ld [wRaditzUnlocked], a
    ret

; -----------------------------------------------------------------------------
; SRAM Variables
; -----------------------------------------------------------------------------

SECTION "Raditz Unlock SRAM", SRAM

sBossesDefeatedNoDeath:: ds 1
sRaditzUnlockProgress:: ds 1
sRaditzUnlocked:: ds 1

ENDS
