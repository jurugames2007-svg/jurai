; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; New Game+ Mode
; Phase 117: Replayability Feature
; -----------------------------------------------------------------------------
; FEATURES:
; - Start with all characters and items unlocked
; - Enemies have +20% HP and +15% ATK
; - All DLC content available from the start
; - Hidden bosses unlocked
; - New Game+ exclusive enemies and items
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

NEW_GAME_PLUS_FLAG equ 0  ; Bit 0 in wGameFlags

; Enemy stat modifiers for New Game+
NGP_HP_MODIFIER equ 20    ; +20% HP
NGP_ATK_MODIFIER equ 15   ; +15% ATK
NGP_DEF_MODIFIER equ 10   ; +10% DEF (for New Game+ exclusive enemies)

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "New Game+ Variables", WRAM

wNewGamePlusActive:: ds 1  ; Flag: 1 if New Game+ mode is active
wNGPEnemyHPBonus:: ds 1   ; Enemy HP bonus percentage
wNGPEnemyATKBonus:: ds 1  ; Enemy ATK bonus percentage

ENDS

; -----------------------------------------------------------------------------
; Initialize New Game+
; -----------------------------------------------------------------------------

InitNewGamePlus::
    push af
    push bc
    push hl
    
    ; Check if New Game+ is available (game must be completed)
    ld a, [wGameCompleted]
    and a
    jr z, .not_available
    
    ; Set New Game+ flag
    ld a, 1
    ld [wNewGamePlusActive], a
    
    ; Set enemy modifiers
    ld a, NGP_HP_MODIFIER
    ld [wNGPEnemyHPBonus], a
    ld a, NGP_ATK_MODIFIER
    ld [wNGPEnemyATKBonus], a
    
    ; Unlock all characters
    ld a, %11111111
    ld [wUnlockedCharacters], a
    
    ; Unlock all items
    ld a, %11111111
    ld [wUnlockedItems], a
    
    ; Give player starting items
    call GiveNGPStartingItems
    
    ; Set starting level for characters
    call SetNGPStartingLevels
    
    ; Show New Game+ message
    ld hl, NewGamePlusMessage
    call ShowTextBox
    call PrintText
    
.not_available:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Give New Game+ Starting Items
; -----------------------------------------------------------------------------

GiveNGPStartingItems::
    push af
    push bc
    
    ; Give all DLC weapons
    ld a, ITEM_FUTURE_TRUNKS_SWORD
    call AddItemToInventory
    ld a, ITEM_SSG_ARMOR
    call AddItemToInventory
    ld a, ITEM_SAIYAN_GAUNTLET
    call AddItemToInventory
    
    ; Give healing items
    ld a, ITEM_SENZU_BEAN
    ld b, 5
    call AddItemWithQuantity
    
    ld a, ITEM_HEALING_ITEMS
    ld b, 10
    call AddItemWithQuantity
    
    ; Give key items
    ld a, ITEM_SCANNER
    call AddItemToInventory
    ld a, ITEM_GRAVITY_DEVICE
    call AddItemToInventory
    
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Set New Game+ Starting Levels
; -----------------------------------------------------------------------------

SetNGPStartingLevels::
    push af
    push bc
    push hl
    
    ; Set all characters to level 30
    ld b, NUM_PLAYABLE_CHARACTERS
    ld hl, wCharacterLevels
    ld a, 30
.level_loop:
    ld [hli], a
    dec b
    jr nz, .level_loop
    
    ; Give characters some starting EXP
    ld b, NUM_PLAYABLE_CHARACTERS
    ld hl, wCharacterEXP
    ld a, 50
    ld c, 0
.exp_loop:
    ld [hli], a
    ld [hli], c
    dec b
    jr nz, .exp_loop
    
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Apply New Game+ Enemy Modifiers
; Called when loading enemy stats
; Input: hl = pointer to enemy stats
; -----------------------------------------------------------------------------

ApplyNGPEnemyModifiers::
    push af
    push bc
    push de
    push hl
    
    ; Check if New Game+ is active
    ld a, [wNewGamePlusActive]
    and a
    jr z, .no_ngp
    
    ; Apply HP modifier
    ld a, [hl+2]  ; HP low byte
    ld b, [hl+3]  ; HP high byte
    call ApplyPercentageIncrease
    ld [hl+2], a
    ld [hl+3], b
    
    ; Apply ATK modifier
    ld a, [hl+4]  ; ATK low byte
    ld b, [hl+5]  ; ATK high byte
    call ApplyPercentageIncrease
    ld [hl+4], a
    ld [hl+5], b
    
.no_ngp:
    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Apply Percentage Increase
; Input: ab = value, wNGPEnemyHPBonus or wNGPEnemyATKBonus = percentage
; Output: ab = increased value
; -----------------------------------------------------------------------------

ApplyPercentageIncrease::
    push af
    push bc
    push de
    push hl
    
    ; Get percentage (0-100)
    ld c, [wNGPEnemyHPBonus]
    
    ; Multiply value by (100 + percentage)
    ; value * (100 + p) / 100
    
    ; Convert ab to 16-bit value in de
    ld d, b
    ld e, a
    
    ; Add percentage to 100
    ld a, 100
    add a, c
    ld c, a
    
    ; Multiply de by c
    call Multiply16x8
    
    ; Divide by 100
    ld a, h
    ld b, l
    call Divide16By100
    
    ; Result in ab
    ld a, b
    ld b, c
    
    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Multiply 16-bit by 8-bit
; Input: de = 16-bit, c = 8-bit
; Output: hl = 24-bit result
; -----------------------------------------------------------------------------

Multiply16x8::
    push af
    push bc
    
    xor a
    ld h, a
    ld l, a
    
    ld b, 8
.multiply_loop:
    srl c
    jr nc, .no_add
    
    add hl, de
    
.no_add:
    sla e
    rl d
    
    dec b
    jr nz, .multiply_loop
    
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Divide 24-bit by 100
; Input: hl = 24-bit value
; Output: bc = 16-bit result
; -----------------------------------------------------------------------------

Divide16By100::
    push af
    push de
    push hl
    
    ; Simple division by 100 for small values
    ; For larger values, this would need a better implementation
    
    ; Shift right by 7 (approx /128) then adjust
    ; This is a simplified approximation
    
    ld a, h
    ld b, l
    
    ; Divide by 100 using repeated subtraction
    xor c
.divide_loop:
    ld de, 100
    call Compare16DE
    jr c, .done_divide
    
    inc c
    
    ; Subtract 100 from ab
    ld a, b
    sub a, e
    ld b, a
    ld a, h
    sbc a, d
    ld h, a
    
    jr .divide_loop

.done_divide:
    ; Result in bc
    ld a, c
    ld b, 0
    
    pop hl
    pop de
    pop af
    ret

; -----------------------------------------------------------------------------
; Compare 16-bit DE with HL
; Output: carry set if HL >= DE
; -----------------------------------------------------------------------------

Compare16DE::
    ld a, h
    cp d
    jr c, .less
    jr nz, .greater_or_equal
    ld a, l
    cp e
    jr c, .less

.greater_or_equal:
    scf
    ret

.less:
    or a
    ret

; -----------------------------------------------------------------------------
; New Game+ Exclusive Content
; -----------------------------------------------------------------------------

; New Game+ exclusive enemies
NGPEnemies::
    ; Format: enemy_id, name, stats
    db ENEMY_GOLDEN_FRIEZA, "Golden Frieza", 0
    dw SPRITE_GOLDEN_FRIEZA
    db LEVEL_80
    dw HP_8000
    dw ATK_400
    dw DEF_300
    db 0
    
    db ENEMY_ULTIMATE_CELL, "Ultimate Cell", 0
    dw SPRITE_ULTIMATE_CELL
    db LEVEL_85
    dw HP_9000
    dw ATK_450
    dw DEF_350
    db 0
    
    db 255  ; End marker

; New Game+ exclusive items
NGPItems::
    ; Format: item_id, name, description
    db ITEM_GOD_ARMOR, "God Armor", 0
    db "Armor fit for", $0A
    db "a god. +200 DEF", $FF
    dw 0, 200, 0  ; ATK, DEF, SPD bonuses
    db 0
    
    db ITEM_INFINITE_SENZU, "Infinite Senzu", 0
    db "A Senzu Bean", $0A
    db "that never", $0A
    db "runs out.", $FF
    db 0
    
    db 255  ; End marker

; -----------------------------------------------------------------------------
; Check If New Game+ Is Active
; Output: carry set if active
; -----------------------------------------------------------------------------

IsNewGamePlusActive::
    push af
    
    ld a, [wNewGamePlusActive]
    and a
    jr z, .not_active
    
    scf
    jr .done

.not_active:
    or a

.done:
    pop af
    ret

; -----------------------------------------------------------------------------
; Save/Load New Game+ Status
; -----------------------------------------------------------------------------

SaveNewGamePlusStatus::
    ld a, [wNewGamePlusActive]
    ld [sNewGamePlusActive], a
    ret

LoadNewGamePlusStatus::
    ld a, [sNewGamePlusActive]
    ld [wNewGamePlusActive], a
    ret

; -----------------------------------------------------------------------------
; SRAM Variables
; -----------------------------------------------------------------------------

SECTION "New Game+ SRAM", SRAM

sNewGamePlusActive:: ds 1

ENDS

; -----------------------------------------------------------------------------
; Messages
; -----------------------------------------------------------------------------

NewGamePlusMessage::
    db "NEW GAME+ MODE", $0A
    db "", $0A
    db "All characters and", $0A
    db "items are unlocked!", $0A
    db "", $0A
    db "Enemies are", $0A
    db "stronger than", $0A
    db "before.", $FF

NewGamePlusUnavailableMessage::
    db "You must complete", $0A
    db "the game first to", $0A
    db "unlock New Game+.", $FF

; -----------------------------------------------------------------------------
; Menu Integration
; -----------------------------------------------------------------------------

; Add New Game+ option to main menu
AddNewGamePlusToMenu::
    push af
    push hl
    
    ; Find the "New Game" option
    ld hl, MainMenuOptions
    ld a, [hl]
    cp "N"
    jr nz, .find_next
    inc hl
    ld a, [hl]
    cp "e"
    jr nz, .find_next
    inc hl
    ld a, [hl]
    cp "w"
    jr nz, .find_next
    
    ; Found "New Game", insert New Game+ after it
    ld de, 3  ; Length of "New Game"
    add hl, de
    
    ; Check if there's space (this is simplified)
    ; In a real implementation, we'd need to shift other options
    
    ; For now, just add it at the end
    ld hl, MainMenuOptions
    
.find_end:
    ld a, [hl]
    cp 0
    jr z, .found_end
    inc hl
    jr .find_end
    
.found_end:
    ; Add New Game+ option
    ld a, "N"
    ld [hli], a
    ld a, "e"
    ld [hli], a
    ld a, "w"
    ld [hli], a
    ld a, " "
    ld [hli], a
    ld a, "G"
    ld [hli], a
    ld a, "a"
    ld [hli], a
    ld a, "m"
    ld [hli], a
    ld a, "e"
    ld [hli], a
    ld a, "+"
    ld [hli], a
    ld a, 0
    ld [hl], a
    
    pop hl
    pop af
    ret

.find_next:
    inc hl
    jr .find_next

; -----------------------------------------------------------------------------
; Handle New Game+ Selection
; -----------------------------------------------------------------------------

HandleNewGamePlusSelection::
    push af
    
    ; Check if game is completed
    ld a, [wGameCompleted]
    and a
    jr z, .not_completed
    
    ; Start New Game+
    call InitNewGamePlus
    call StartNewGame
    jr .done
    
.not_completed:
    ; Show unavailable message
    ld hl, NewGamePlusUnavailableMessage
    call ShowTextBox
    call PrintText
    
.done:
    pop af
    ret
