; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; Hidden Item: Future Trunks' Sword Puzzle
; Phase 117: Hidden Content
; -----------------------------------------------------------------------------
; LOCATION: Time Room
; PUZZLE: Activate 3 panels in the correct order (1-3-2)
; REWARD: Future Trunks' Sword (+50 ATK, +30 DEF)
; -----------------------------------------------------------------------------
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

; Panel IDs
PANEL_1 equ 0
PANEL_2 equ 1
PANEL_3 equ 2

; Panel states
PANEL_INACTIVE equ 0
PANEL_ACTIVE equ 1
PANEL_COMPLETED equ 2

; Puzzle states
PUZZLE_INACTIVE equ 0
PUZZLE_STARTED equ 1
PUZZLE_COMPLETED equ 2

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "Trunks Sword Puzzle Variables", WRAM

wPanelStates:: ds 3  ; States for panels 1, 2, 3
wPuzzleState:: ds 1  ; Current puzzle state
wPuzzleProgress:: ds 1  ; Current progress (0-3)
wHasFutureTrunksSword:: ds 1  ; Flag: 1 if player has the sword

ENDS

; -----------------------------------------------------------------------------
; Initialize Puzzle
; -----------------------------------------------------------------------------

InitTrunksSwordPuzzle::
    push af
    
    ; Reset all panel states
    xor a
    ld [wPanelStates+0], a
    ld [wPanelStates+1], a
    ld [wPanelStates+2], a
    
    ; Reset puzzle state
    ld [wPuzzleState], a
    ld [wPuzzleProgress], a
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Check Panel Interaction
; Called when player interacts with a panel
; Input: a = panel ID (0-2)
; -----------------------------------------------------------------------------

CheckPanelInteraction::
    push af
    push bc
    push hl
    
    ; Check if puzzle is already completed
    ld a, [wPuzzleState]
    cp PUZZLE_COMPLETED
    jr z, .puzzle_complete
    
    ; Check if player already has the sword
    ld a, [wHasFutureTrunksSword]
    and a
    jr nz, .already_has_sword
    
    ; Check which panel was activated
    cp PANEL_1
    jr z, .panel_1
    cp PANEL_2
    jr z, .panel_2
    cp PANEL_3
    jr z, .panel_3
    jr .invalid_panel

.panel_1:
    ; Check if this is the expected panel
    ld a, [wPuzzleProgress]
    and a
    jr nz, .wrong_order  ; Expected panel 1 first
    
    ; Activate panel 1
    ld a, PANEL_ACTIVE
    ld [wPanelStates+0], a
    
    ; Increment progress
    ld a, 1
    ld [wPuzzleProgress], a
    
    ; Start puzzle if not already started
    ld a, [wPuzzleState]
    and a
    jr nz, .check_completion
    ld a, PUZZLE_STARTED
    ld [wPuzzleState], a
    
    jr .check_completion

.panel_2:
    ; Check expected progress
    ld a, [wPuzzleProgress]
    cp 2
    jr nz, .wrong_order  ; Expected panel 2 third
    
    ; Activate panel 2
    ld a, PANEL_ACTIVE
    ld [wPanelStates+1], a
    
    ; Increment progress
    ld a, 3
    ld [wPuzzleProgress], a
    
    jr .check_completion

.panel_3:
    ; Check expected progress
    ld a, [wPuzzleProgress]
    cp 1
    jr nz, .wrong_order  ; Expected panel 3 second
    
    ; Activate panel 3
    ld a, PANEL_ACTIVE
    ld [wPanelStates+2], a
    
    ; Increment progress
    ld a, 2
    ld [wPuzzleProgress], a
    
    jr .check_completion

.wrong_order:
    ; Wrong panel activated - reset puzzle
    call ResetPuzzle
    
    ; Show error message
    ld hl, WrongOrderMessage
    call ShowTextBox
    call PrintText
    jr .done

.check_completion:
    ; Check if puzzle is complete
    ld a, [wPuzzleProgress]
    cp 3
    jr nz, .done
    
    ; Puzzle complete!
    call CompletePuzzle

.done:
    pop hl
    pop bc
    pop af
    ret

.puzzle_complete:
    ; Puzzle already completed
    ld hl, PuzzleAlreadyCompleteMessage
    call ShowTextBox
    call PrintText
    jr .done

.already_has_sword:
    ; Player already has the sword
    ld hl, AlreadyHasSwordMessage
    call ShowTextBox
    call PrintText
    jr .done

.invalid_panel:
    ; Invalid panel ID
    jr .done

; -----------------------------------------------------------------------------
; Reset Puzzle
; -----------------------------------------------------------------------------

ResetPuzzle::
    push af
    
    ; Reset all panel states
    xor a
    ld [wPanelStates+0], a
    ld [wPanelStates+1], a
    ld [wPanelStates+2], a
    
    ; Reset progress
    ld [wPuzzleProgress], a
    
    ; Reset puzzle state
    ld [wPuzzleState], a
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Complete Puzzle
; -----------------------------------------------------------------------------

CompletePuzzle::
    push af
    
    ; Mark puzzle as completed
    ld a, PUZZLE_COMPLETED
    ld [wPuzzleState], a
    
    ; Give the player the sword
    ld a, 1
    ld [wHasFutureTrunksSword], a
    
    ; Add sword to inventory
    ld a, ITEM_FUTURE_TRUNKS_SWORD
    call AddItemToInventory
    
    ; Show completion message
    ld hl, PuzzleCompleteMessage
    call ShowTextBox
    call PrintText
    
    ; Play fanfare
    ld a, SOUND_FANFARE_ITEM
    call PlaySound
    
    ; Spawn the sword in the world
    ld a, 10
    ld [wSpawnX], a
    ld a, 5
    ld [wSpawnY], a
    ld a, ITEM_FUTURE_TRUNKS_SWORD
    ld [wItemToSpawn], a
    call SpawnItem
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Messages
; -----------------------------------------------------------------------------

WrongOrderMessage::
    db "The panels must be", $0A
    db "activated in the", $0A
    db "correct order:", $0A
    db "1, then 3, then 2.", $FF

PuzzleAlreadyCompleteMessage::
    db "The puzzle is", $0A
    db "already complete.", $FF

AlreadyHasSwordMessage::
    db "You already have", $0A
    db "Future Trunks'", $0A
    db "Sword.", $FF

PuzzleCompleteMessage::
    db "Puzzle complete!", $0A
    db "", $0A
    db "You obtained", $0A
    db "Future Trunks'", $0A
    db "Sword!", $0A
    db "", $0A
    db "+50 ATK, +30 DEF", $FF

; -----------------------------------------------------------------------------
; Check If Player Has Sword
; Output: carry set if has sword
; -----------------------------------------------------------------------------

HasFutureTrunksSword::
    push af
    
    ld a, [wHasFutureTrunksSword]
    and a
    jr z, .no_sword
    
    scf
    jr .done

.no_sword:
    or a

.done:
    pop af
    ret

; -----------------------------------------------------------------------------
; Save/Load Puzzle State
; -----------------------------------------------------------------------------

SaveTrunksSwordPuzzle::
    ; Save to SRAM
    ld a, [wPanelStates+0]
    ld [sPanelStates+0], a
    ld a, [wPanelStates+1]
    ld [sPanelStates+1], a
    ld a, [wPanelStates+2]
    ld [sPanelStates+2], a
    ld a, [wPuzzleState]
    ld [sPuzzleState], a
    ld a, [wPuzzleProgress]
    ld [sPuzzleProgress], a
    ld a, [wHasFutureTrunksSword]
    ld [sHasFutureTrunksSword], a
    ret

LoadTrunksSwordPuzzle::
    ; Load from SRAM
    ld a, [sPanelStates+0]
    ld [wPanelStates+0], a
    ld a, [sPanelStates+1]
    ld [wPanelStates+1], a
    ld a, [sPanelStates+2]
    ld [wPanelStates+2], a
    ld a, [sPuzzleState]
    ld [wPuzzleState], a
    ld a, [sPuzzleProgress]
    ld [wPuzzleProgress], a
    ld a, [sHasFutureTrunksSword]
    ld [wHasFutureTrunksSword], a
    ret

; -----------------------------------------------------------------------------
; SRAM Variables
; -----------------------------------------------------------------------------

SECTION "Trunks Sword Puzzle SRAM", SRAM

sPanelStates:: ds 3
sPuzzleState:: ds 1
sPuzzleProgress:: ds 1
sHasFutureTrunksSword:: ds 1

ENDS

; -----------------------------------------------------------------------------
; Panel Interaction Hook
; Called when player interacts with an object in the Time Room
; -----------------------------------------------------------------------------

TimeRoomPanelHook::
    push af
    
    ; Check if this is one of our panels
    ld a, [wCurrentObjectID]
    cp OBJ_TIME_ROOM_PANEL_1
    jr z, .panel_1_activated
    cp OBJ_TIME_ROOM_PANEL_2
    jr z, .panel_2_activated
    cp OBJ_TIME_ROOM_PANEL_3
    jr z, .panel_3_activated
    jr .not_panel

.panel_1_activated:
    ld a, PANEL_1
    call CheckPanelInteraction
    jr .done

.panel_2_activated:
    ld a, PANEL_2
    call CheckPanelInteraction
    jr .done

.panel_3_activated:
    ld a, PANEL_3
    call CheckPanelInteraction
    jr .done

.not_panel:
    ; Not one of our panels - call original handler
    call OriginalObjectInteractionHandler

.done:
    pop af
    ret

; -----------------------------------------------------------------------------
; Future Trunks' Sword Item Data
; -----------------------------------------------------------------------------

ItemFutureTrunksSword::
    db "F.Trunks Sword", 0  ; Name
    db ITEM_TYPE_WEAPON    ; Type
    db WEAPON_TYPE_SWORD   ; Subtype
    dw 50                  ; ATK bonus
    dw 30                  ; DEF bonus (unusual for a weapon, but this is special)
    dw 0                   ; SPD bonus
    db 0                   ; Element
    db 100                 ; Durability
    db 0                   ; Weight
    dw 5000                ; Sell price
    db "A sword from the", $0A
    db "future, wielded", $0A
    db "by Trunks.", $FF   ; Description
