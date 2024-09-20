from matplotlib.pyplot import figure, show, tight_layout
from mpl_toolkits.mplot3d import Axes3D
from numpy import array
from numpy.random import rand

TEXT_COLOR = "black"
FIGSIZE = (14, 8)
# Example parameterized input for the phases and dependencies
PHASES = [
    (0, 2, "Planning"),
    (2, 5, "Development"),
    (5, 7, "Testing"),
    (7, 9, "Deployment"),
]
DEPENDENCIES = [
    (0, 1),  # Planning -> Development
    (1, 2),  # Development -> Testing
    (2, 3),  # Testing -> Deployment
]


def draw_bar(
    ax: Axes3D,
    x: float,
    y: float,
    z: float,
    dx: float,
    dy: float,
    dz: float,
    color: str,
    edge_color: str = None,
) -> None:
    # Draw the sides of the bar with adjusted alpha for better visibility
    edge_color = color if edge_color is None else edge_color
    ax.bar3d(
        x, y, z, dx, dy, dz, shade=True, color=color, edgecolor=edge_color, alpha=0.8
    )


# Enhanced function to draw dependencies between bars
def draw_dependency(
    ax: Axes3D,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    z: float,
    dz: float,
) -> None:
    # Points for the start and end
    points = array([[start_x, start_y, z + dz], [end_x, end_y, z + dz]])
    # Draw a line between the two points
    ax.plot3D(points[:, 0], points[:, 1], points[:, 2], "gray")


# Adjusting the draw_label function to improve text legibility
def draw_label(
    ax: Axes3D, x: float, y: float, z: float, text: str, dz: float, max_phases: int
) -> None:
    # Calculate the scale for the text size based on the number of phases
    text_scale = max(1, 10 / max_phases)
    ax.text(
        x,
        y,
        z + dz,
        text,
        zdir="y",
        va="center",
        ha="center",
        size=text_scale * 8,
        color=TEXT_COLOR,
    )


# Updating the create_gantt_chart function to improve the overall layout and scaling
def create_gantt_chart(
    phases: list[tuple[int, int, str]] = PHASES,
    dependencies: list[tuple[int, int]] = DEPENDENCIES,
    figsize: tuple[int, int] = FIGSIZE,
    toshow: bool = True,
) -> None:
    fig = figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    # Determine the max width (dy) based on the number of phases
    max_phases = len(phases)
    dy = max(0.8, 10 / max_phases)

    # Calculate the maximum time based on the latest end time and the maximum z based on the number of dependencies
    max_time = max(end for _, end, _ in phases)
    max_z = 1 + len(dependencies) * 0.1
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, max_phases * dy)
    ax.set_zlim(0, max_z)

    # Define the depth of the bars (dz)
    dz = 0.1

    # Draw the bars and labels for each phase
    for i, phase in enumerate(phases):
        dz *= 2
        start, end, label = phase
        draw_bar(
            ax,
            start,
            i * dy,
            0,
            end - start,
            dy,
            dz,
            rand(
                3,
            ),
            #'white'
        )
        draw_label(
            ax, (start + end) / 2, i * dy + dy / 2, dz, label, dz * 0.75, max_phases
        )

    # Draw dependencies
    for dep_num, dependency in enumerate(dependencies):
        start_phase, end_phase = dependency
        start_x, start_y = (phases[start_phase][1], start_phase * dy + dy / 2)
        end_x, end_y = (phases[end_phase][0], end_phase * dy + dy / 2)
        draw_dependency(ax, start_x, start_y, end_x, end_y, dep_num * 0.1, dz * 0.75)

    # Set the labels for the axes and improve the appearance of the grid and background
    ax.set_xlabel("Time")
    ax.set_ylabel("Phases")
    ax.set_zlabel("")
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(True)

    # Adjust the view angle for better visibility
    ax.view_init(elev=30, azim=30)

    # Show the plot with a tight layout
    tight_layout()
    if toshow:
        show()


if __name__ == "__main__":
    create_gantt_chart()
