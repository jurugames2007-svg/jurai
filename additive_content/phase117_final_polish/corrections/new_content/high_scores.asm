; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; High Score System
; Phase 117: Replayability Feature
; -----------------------------------------------------------------------------
; FEATURES:
; - Tracks times for Any% and 100% completion
; - Tracks high scores for side quests
; - Tracks combat records (max combo, etc.)
; - Saves to SRAM
; - Top 10 scores per category
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

; Score categories
SCORE_CATEGORY_ANY_PERCENT equ 0
SCORE_CATEGORY_100_PERCENT equ 1
SCORE_CATEGORY_QUEST_SCORE equ 2
SCORE_CATEGORY_MAX_COMBO equ 3
SCORE_CATEGORY_BOSS_RUSH equ 4

NUM_CATEGORIES equ 5
NUM_SCORES_PER_CATEGORY equ 10
SCORE_ENTRY_SIZE equ 7  ; 3 bytes name + 4 bytes score/time

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "High Score Variables", WRAM

wCurrentScoreCategory:: ds 1  ; Category being viewed/updated
wScoreBuffer:: ds SCORE_ENTRY_SIZE  ; Temporary score buffer

ENDS

; -----------------------------------------------------------------------------
; High Score Table (in SRAM)
; -----------------------------------------------------------------------------

SECTION "High Score Table", SRAM

sHighScores::
    ds NUM_CATEGORIES * NUM_SCORES_PER_CATEGORY * SCORE_ENTRY_SIZE

ENDS

; -----------------------------------------------------------------------------
; Initialize High Scores
; -----------------------------------------------------------------------------

InitHighScores::
    push af
    push bc
    push hl

    ; Clear high score table if it's corrupted
    ; (In a real implementation, check for a magic number)
    
    ; For now, just initialize with default values
    ld hl, sHighScores
    ld bc, NUM_CATEGORIES * NUM_SCORES_PER_CATEGORY * SCORE_ENTRY_SIZE
    xor a
.init_loop:
    ld [hli], a
    dec bc
    ld a, b
    or c
    jr nz, .init_loop

    ; Set default "no score" entries
    call SetDefaultScores

    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Set Default Scores
; -----------------------------------------------------------------------------

SetDefaultScores::
    push af
    push bc
    push de
    push hl

    ld de, sHighScores
    ld b, NUM_CATEGORIES
.category_loop:
    push bc
    
    ld c, NUM_SCORES_PER_CATEGORY
.entry_loop:
    push bc
    
    ; Set name to "---"
    ld a, "-"
    ld [de], a
    inc de
    ld [de], a
    inc de
    ld [de], a
    inc de
    
    ; Set score to 0 (or max time for time-based categories)
    xor a
    ld [de], a
    inc de
    ld [de], a
    inc de
    ld [de], a
    inc de
    ld [de], a
    inc de
    
    pop bc
    dec c
    jr nz, .entry_loop
    
    pop bc
    dec b
    jr nz, .category_loop

    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Submit Score
; Input: a = category, hl = name (3 bytes), de = score/time (4 bytes)
; -----------------------------------------------------------------------------

SubmitScore::
    push af
    push bc
    push de
    push hl

    ; Store category
    ld [wCurrentScoreCategory], a
    
    ; Copy name to buffer
    ld bc, 3
    call memcpy
    
    ; Copy score to buffer + 3
    ld hl, wScoreBuffer + 3
    ld bc, 4
    call memcpy
    
    ; Find position in table
    call FindScorePosition
    
    ; If position is valid, insert the score
    cp 255
    jr z, .not_high_score
    
    ; Insert the score
    call InsertScore
    
    ; Save to SRAM
    call SaveHighScores
    
    ; Show "New High Score!" message
    ld hl, NewHighScoreMessage
    call ShowTextBox
    call PrintText
    
.not_high_score:
    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Find Score Position
; Output: a = position (0-9) or 255 if not a high score
; -----------------------------------------------------------------------------

FindScorePosition::
    push bc
    push de
    push hl

    ; Calculate table offset for this category
    ld a, [wCurrentScoreCategory]
    ld b, NUM_SCORES_PER_CATEGORY
    ld c, SCORE_ENTRY_SIZE
    call MultiplyABC
    ld hl, sHighScores
    add hl, de
    
    ; Check each score in the category
    ld b, NUM_SCORES_PER_CATEGORY
    ld c, 0  ; position counter
    
.check_loop:
    push bc
    
    ; Compare score at hl+3 with score in buffer+3
    ld de, wScoreBuffer + 3
    call CompareScores
    jr c, .found_position  ; If buffer score is better
    
    ; Move to next entry
    ld de, SCORE_ENTRY_SIZE
    add hl, de
    
    pop bc
    inc c
    dec b
    jr nz, .check_loop
    
    ; Not a high score
    ld a, 255
    jr .done

.found_position:
    pop bc
    ld a, c

.done:
    pop hl
    pop de
    pop bc
    ret

; -----------------------------------------------------------------------------
; Compare Scores
; Input: hl = score 1 (4 bytes), de = score 2 (4 bytes)
; Output: carry set if score 1 < score 2
; Notes: For time-based categories, lower is better
;        For score-based categories, higher is better
; -----------------------------------------------------------------------------

CompareScores::
    push af
    push bc
    push hl

    ; Check category type
    ld a, [wCurrentScoreCategory]
    cp SCORE_CATEGORY_ANY_PERCENT
    jr z, .time_category
    cp SCORE_CATEGORY_100_PERCENT
    jr z, .time_category
    cp SCORE_CATEGORY_BOSS_RUSH
    jr z, .time_category
    
    ; Score category - higher is better
    call CompareScoreHigher
    jr .done

.time_category:
    ; Time category - lower is better
    call CompareScoreLower

.done:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Compare Score (Higher is Better)
; -----------------------------------------------------------------------------

CompareScoreHigher::
    ; Compare 4-byte values at hl and de
    ; Set carry if [hl] < [de]
    
    ld a, [de+3]
    cp [hl+3]
    jr c, .less
    jr nz, .greater
    
    ld a, [de+2]
    cp [hl+2]
    jr c, .less
    jr nz, .greater
    
    ld a, [de+1]
    cp [hl+1]
    jr c, .less
    jr nz, .greater
    
    ld a, [de]
    cp [hl]
    jr c, .less

.greater:
    or a
    ret

.less:
    scf
    ret

; -----------------------------------------------------------------------------
; Compare Score (Lower is Better)
; -----------------------------------------------------------------------------

CompareScoreLower::
    ; Compare 4-byte values at hl and de
    ; Set carry if [hl] > [de]
    
    ld a, [hl+3]
    cp [de+3]
    jr c, .less
    jr nz, .greater
    
    ld a, [hl+2]
    cp [de+2]
    jr c, .less
    jr nz, .greater
    
    ld a, [hl+1]
    cp [de+1]
    jr c, .less
    jr nz, .greater
    
    ld a, [hl]
    cp [de]
    jr c, .less

.greater:
    scf
    ret

.less:
    or a
    ret

; -----------------------------------------------------------------------------
; Insert Score
; Input: a = position (0-9)
; -----------------------------------------------------------------------------

InsertScore::
    push af
    push bc
    push de
    push hl

    ; Calculate table offset
    ld b, a  ; position
    ld a, [wCurrentScoreCategory]
    ld c, NUM_SCORES_PER_CATEGORY
    ld d, SCORE_ENTRY_SIZE
    call MultiplyABC
    add a, e
    ld e, a
    add a, d
    ld d, a
    ld hl, sHighScores
    add hl, de
    
    ; Shift scores down to make room
    ld b, NUM_SCORES_PER_CATEGORY - 1
    sub b
    jr z, .no_shift
    
.shift_loop:
    push bc
    
    ; Copy entry at hl to hl + SCORE_ENTRY_SIZE
    push hl
    ld de, SCORE_ENTRY_SIZE
    add hl, de
    ex de, hl
    pop hl
    ld bc, SCORE_ENTRY_SIZE
    call memcpy
    
    ; Move to next entry
    ld de, SCORE_ENTRY_SIZE
    add hl, de
    
    pop bc
    dec b
    jr nz, .shift_loop

.no_shift:
    ; Copy new score to position
    ld de, wScoreBuffer
    ld bc, SCORE_ENTRY_SIZE
    call memcpy

    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Multiply A * B * C
; Output: de = result
; -----------------------------------------------------------------------------

MultiplyABC::
    push af
    push bc
    push hl

    ; Multiply a * b first
    ld h, 0
    ld l, a
    
    ld a, b
    and a
    jr z, .zero_result
    
.multiply_ab:
    add hl, hl
    dec a
    jr nz, .multiply_ab
    
    ; Now multiply by c
    ld a, c
    and a
    jr z, .done
    
.multiply_c:
    add hl, hl
    dec a
    jr nz, .multiply_c
    
.done:
    ld d, h
    ld e, l
    jr .exit

.zero_result:
    xor a
    ld d, a
    ld e, a

.exit:
    pop hl
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Save High Scores to SRAM
; -----------------------------------------------------------------------------

SaveHighScores::
    ; High scores are already in SRAM, but we need to mark it as valid
    ; In a real implementation, we'd write a magic number
    ret

; -----------------------------------------------------------------------------
; Load High Scores from SRAM
; -----------------------------------------------------------------------------

LoadHighScores::
    ; High scores are in SRAM, just need to verify
    ; In a real implementation, check magic number
    ret

; -----------------------------------------------------------------------------
; Display High Scores
; Input: a = category to display
; -----------------------------------------------------------------------------

DisplayHighScores::
    push af
    push bc
    push de
    push hl

    ; Store category
    ld [wCurrentScoreCategory], a
    
    ; Calculate table offset
    ld b, a
    ld c, NUM_SCORES_PER_CATEGORY
    ld d, SCORE_ENTRY_SIZE
    call MultiplyABC
    ld hl, sHighScores
    add hl, de
    
    ; Display category title
    call GetCategoryTitle
    call ShowTextBox
    call PrintText
    
    ; Display each score
    ld b, NUM_SCORES_PER_CATEGORY
    ld c, 1  ; Rank counter

.score_loop:
    push bc
    
    ; Display rank
    ld a, c
    call DisplayRank
    
    ; Display name
    ld a, [hli]
    call PrintChar
    ld a, [hli]
    call PrintChar
    ld a, [hli]
    call PrintChar
    inc hl
    
    ; Display separator
    ld a, ":"
    call PrintChar
    ld a, " "
    call PrintChar
    
    ; Display score/time
    call DisplayScoreValue
    
    ; New line
    call NewLine
    
    pop bc
    inc hl
    inc hl
    inc hl
    inc hl
    inc c
    dec b
    jr nz, .score_loop

    ; Wait for player to press a button
    call WaitForButtonPress

    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Get Category Title
; Output: hl = pointer to title text
; -----------------------------------------------------------------------------

GetCategoryTitle::
    ld a, [wCurrentScoreCategory]
    cp SCORE_CATEGORY_ANY_PERCENT
    jr z, .any_percent
    cp SCORE_CATEGORY_100_PERCENT
    jr z, .hundred_percent
    cp SCORE_CATEGORY_QUEST_SCORE
    jr z, .quest_score
    cp SCORE_CATEGORY_MAX_COMBO
    jr z, .max_combo
    cp SCORE_CATEGORY_BOSS_RUSH
    jr z, .boss_rush
    
    ; Default
    ld hl, DefaultTitle
    ret

.any_percent:
    ld hl, AnyPercentTitle
    ret

.hundred_percent:
    ld hl, HundredPercentTitle
    ret

.quest_score:
    ld hl, QuestScoreTitle
    ret

.max_combo:
    ld hl, MaxComboTitle
    ret

.boss_rush:
    ld hl, BossRushTitle
    ret

; -----------------------------------------------------------------------------
; Titles
; -----------------------------------------------------------------------------

AnyPercentTitle:
    db "ANY% TIME", $FF

HundredPercentTitle:
    db "100% TIME", $FF

QuestScoreTitle:
    db "QUEST SCORE", $FF

MaxComboTitle:
    db "MAX COMBO", $FF

BossRushTitle:
    db "BOSS RUSH", $FF

DefaultTitle:
    db "HIGH SCORES", $FF

; -----------------------------------------------------------------------------
; Display Rank
; Input: a = rank (1-10)
; -----------------------------------------------------------------------------

DisplayRank::
    push af
    
    ; Convert rank to text
    cp 10
    jr nz, .not_10
    
    ; Rank 10
    ld a, "1"
    call PrintChar
    ld a, "0"
    call PrintChar
    ld a, "."
    call PrintChar
    jr .done

.not_10:
    ; Rank 1-9
    add a, "0"
    call PrintChar
    ld a, "."
    call PrintChar

.done:
    ld a, " "
    call PrintChar
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Display Score Value
; Input: hl = pointer to score (4 bytes)
; -----------------------------------------------------------------------------

DisplayScoreValue::
    push af
    push hl
    
    ; Check if this is a time category
    ld a, [wCurrentScoreCategory]
    cp SCORE_CATEGORY_ANY_PERCENT
    jr z, .display_time
    cp SCORE_CATEGORY_100_PERCENT
    jr z, .display_time
    cp SCORE_CATEGORY_BOSS_RUSH
    jr z, .display_time
    
    ; Display as number
    call DisplayNumber
    jr .done

.display_time:
    ; Display as time (HH:MM:SS)
    call DisplayTime

.done:
    pop hl
    pop af
    ret

; -----------------------------------------------------------------------------
; Display Number
; Input: hl = pointer to 4-byte number
; -----------------------------------------------------------------------------

DisplayNumber::
    push af
    push bc
    push de
    push hl
    
    ; Convert to decimal string
    ld de, wNumberBuffer
    call UInt32ToString
    
    ; Print the string
    ld hl, wNumberBuffer
    call PrintText
    
    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Display Time
; Input: hl = pointer to 4-byte time in seconds
; -----------------------------------------------------------------------------

DisplayTime::
    push af
    push bc
    push de
    push hl
    
    ; Convert seconds to HH:MM:SS
    call SecondsToTimeString
    
    ; Print the string
    ld hl, wTimeString
    call PrintText
    
    pop hl
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Convert 32-bit Unsigned Integer to String
; Input: hl = pointer to 32-bit value
; Output: de = pointer to null-terminated string
; -----------------------------------------------------------------------------

UInt32ToString::
    push af
    push bc
    push hl

    ; Save input pointer
    push hl
    pop bc
    
    ; Initialize buffer
    ld hl, wNumberBuffer
    ld [hl], 0
    
    ; Check for zero
    ld a, [bc+3]
    or [bc+2]
    or [bc+1]
    or [bc]
    jr z, .zero

    ; Convert to decimal
    ld de, 1000000000
    call .divide
    ld de, 100000000
    call .divide
    ld de, 10000000
    call .divide
    ld de, 1000000
    call .divide
    ld de, 100000
    call .divide
    ld de, 10000
    call .divide
    ld de, 1000
    call .divide
    ld de, 100
    call .divide
    ld de, 10
    call .divide
    ld de, 1
    call .divide
    
    jr .done

.zero:
    ld a, "0"
    ld [hl], a
    inc hl
    ld [hl], 0

.done:
    ld d, h
    ld e, l
    pop hl
    pop bc
    pop af
    ret

.divide:
    push de
    push hl
    
    xor a
    ld b, a
    ld c, a
    
.divide_loop:
    ; Subtract de from bc
    ld a, [bc+3]
    sub a, d
    ld [bc+3], a
    ld a, [bc+2]
    sbc a, e
    ld [bc+2], a
    ld a, [bc+1]
    sbc a, 0
    ld [bc+1], a
    ld a, [bc]
    sbc a, 0
    ld [bc], a
    
    jr c, .divide_done
    
    ; Add to quotient
    inc c
    jr nz, .divide_loop
    inc b
    jr .divide_loop

.divide_done:
    ; Store digit
    ld a, c
    and a
    jr z, .no_digit
    
    add a, "0"
    ld [hl], a
    inc hl

.no_digit:
    pop hl
    pop de
    ret

; -----------------------------------------------------------------------------
; Convert Seconds to Time String (HH:MM:SS)
; Input: hl = pointer to 32-bit seconds
; Output: wTimeString = "HH:MM:SS"
; -----------------------------------------------------------------------------

SecondsToTimeString::
    push af
    push bc
    push de
    push hl

    ; Load seconds into bc:de
    ld a, [hl+3]
    ld b, a
    ld a, [hl+2]
    ld c, a
    ld a, [hl+1]
    ld d, a
    ld a, [hl]
    ld e, a
    
    ; Calculate hours
    ld hl, 0
.hours_loop:
    ld a, e
    sub a, 60
    ld e, a
    ld a, d
    sbc a, 0
    ld d, a
    ld a, c
    sbc a, 0
    ld c, a
    ld a, b
    sbc a, 0
    ld b, a
    
    jr c, .hours_done
    
    inc hl
    jr .hours_loop

.hours_done:
    push hl
    
    ; Calculate minutes
    ld hl, 0
.minutes_loop:
    ld a, e
    sub a, 60
    ld e, a
    ld a, d
    sbc a, 0
    ld d, a
    ld a, c
    sbc a, 0
    ld c, a
    ld a, b
    sbc a, 0
    ld b, a
    
    jr c, .minutes_done
    
    inc hl
    jr .minutes_loop

.minutes_done:
    push hl
    
    ; Seconds = remaining de
    ld a, e
    
    ; Now convert to string
    pop bc  ; bc = seconds
    pop de  ; de = minutes
    pop hl  ; hl = hours
    
    ; Format: HH:MM:SS
    ld a, l
    call .byte_to_decimal
    ld [wTimeString+0], a
    ld [wTimeString+1], a
    
    ld a, ":"
    ld [wTimeString+2], a
    
    ld a, e
    call .byte_to_decimal
    ld [wTimeString+3], a
    ld [wTimeString+4], a
    
    ld a, ":"
    ld [wTimeString+5], a
    
    ld a, c
    call .byte_to_decimal
    ld [wTimeString+6], a
    ld [wTimeString+7], a
    
    ld a, 0
    ld [wTimeString+8], a
    
    pop hl
    pop de
    pop bc
    pop af
    ret

.byte_to_decimal:
    ; Convert a to two decimal digits
    ; Output: a = tens digit, [wTemp] = units digit
    push af
    
    ld b, a
    ld a, 10
    call DivideAB
    
    add a, "0"
    push af
    
    ld a, b
    add a, "0"
    ld [wTemp], a
    
    pop af
    ret

; -----------------------------------------------------------------------------
; Messages
; -----------------------------------------------------------------------------

NewHighScoreMessage::
    db "NEW HIGH SCORE!", $FF

HighScoresMenuText::
    db "HIGH SCORES", $0A
    db "", $0A
    db "1. Any% Time", $0A
    db "2. 100% Time", $0A
    db "3. Quest Score", $0A
    db "4. Max Combo", $0A
    db "5. Boss Rush", $FF

; -----------------------------------------------------------------------------
; Buffers
; -----------------------------------------------------------------------------

SECTION "High Score Buffers", WRAM

wNumberBuffer:: ds 12  ; Buffer for number string
wTimeString:: ds 9    ; Buffer for time string (HH:MM:SS\0)
wTemp:: ds 1          ; Temporary storage

ENDS

; -----------------------------------------------------------------------------
; Multiply 16-bit by 8-bit
; Input: hl = 16-bit, a = 8-bit
; Output: hl = 24-bit result
; -----------------------------------------------------------------------------

Multiply16x8::
    push af
    push bc
    push de

    xor a
    ld d, a
    ld e, a
    
    ld b, 8
    
.multiply_loop:
    srl a
    jr nc, .no_add
    
    add hl, de
    
.no_add:
    sla e
    rl d
    
    dec b
    jr nz, .multiply_loop
    
    pop de
    pop bc
    pop af
    ret

; -----------------------------------------------------------------------------
; Divide A by B
; Input: a = dividend, b = divisor
; Output: a = quotient, b = remainder
; -----------------------------------------------------------------------------

DivideAB::
    push af
    push bc
    
    xor c
    
.divide_loop:
    ld a, b
    sub a, c
    jr c, .divide_done
    
    ld b, a
    inc c
    jr .divide_loop

.divide_done:
    ld a, c
    
    pop bc
    pop af
    ret
