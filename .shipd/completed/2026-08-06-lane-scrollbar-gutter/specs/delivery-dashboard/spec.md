## ADDED Requirements

### Requirement: Stable lane scrollbar gutter
id: lane-scrollbar-gutter

Every lifecycle lane SHALL reserve its vertical scrollbar's column
permanently (a stable scrollbar gutter), so the lane's content width is
identical whether or not the lane currently scrolls, no lane content is ever
laid out or painted in the scrollbar's column, and the appearance or
disappearance of the scrollbar never reflows the lane's rows. The
board-screen sweep SHALL assert that a scrolling lane's group-header buttons
are disjoint from the scrollbar's region and that content width is unchanged
by growth that makes the scrollbar appear.

#### Scenario: Content width is scroll-state independent
- **GIVEN** a board whose shipped lane does not scroll
- **WHEN** the board grows via refresh until the shipped lane's scrollbar
  appears
- **THEN** the lane's scrollable content width is the same before and after

#### Scenario: Buttons never share the scrollbar's column
- **GIVEN** a lane whose vertical scrollbar is displayed
- **WHEN** its group headers render
- **THEN** every header button's region is disjoint from the scrollbar's
  region

#### Scenario: The gutter is reserved while not scrolling
- **GIVEN** a lane with too little content to scroll
- **WHEN** it renders
- **THEN** the scrollbar column is still reserved, and the lane's content
  width equals that of a scrolling lane of the same outer width
