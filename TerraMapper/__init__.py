import lihzahrd, lihzahrd.enums, logging, logging.handlers, yaml, typing, deepzoom
from . import constants
from PIL import Image, ImageDraw


class TerraMapper:
    def __init__(
        self,
        config=None,
        configPath=None,
    ) -> None:
        self.initLogging()
        if config is None and configPath is None:
            raise ValueError("Either config or configPath must be provided")
        if config is not None and configPath is not None:
            raise ValueError("Only one of config or configPath can be provided")
        if config is not None:
            self.log.debug(f"Loading configuration provided via module parameters")
            self.config = config
            self.log.debug(f"Configuration: {self.config}")
        if configPath is not None:
            self.log.debug(f"Loading configuration from {configPath}")
            self.config = self.loadConfig(configPath)
            self.log.debug(f"Configuration: {self.config}")

        self.generateMap()

        if self.config["deep_zoom"]["enabled"] == True:
            self.generateDeepZoomData()

    def initLogging(self):
        self.log = logging.getLogger("TerraMapper")

        logFormatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        stdoutStreamHandler = logging.StreamHandler()
        stdoutStreamHandler.setFormatter(logFormatter)
        syslogStreamHandler = logging.handlers.SysLogHandler()
        syslogStreamHandler.setFormatter(logFormatter)
        self.log.setLevel(logging.DEBUG)

        self.log.addHandler(stdoutStreamHandler)
        self.log.addHandler(syslogStreamHandler)
        self.log.debug("Logging Initialized")

    def loadConfig(self, configPath):
        return yaml.safe_load(open(configPath, "r"))

    def generateMap(self):
        draw_background = self.config["draw"]["background"]
        draw_blocks = self.config["draw"]["blocks"]
        draw_walls = self.config["draw"]["walls"]
        draw_liquids = self.config["draw"]["liquids"]
        draw_wires = self.config["draw"]["wires"]
        draw_paint = self.config["draw"]["paint"]

        min_x = self.config["draw"]["min_x"]
        min_y = self.config["draw"]["min_y"]
        region_width = self.config["draw"]["region_width"]
        region_height = self.config["draw"]["region_height"]

        output_file = self.config["output"]["file_path"]

        self.log.info(f"Draw background layer: {draw_background}")
        self.log.info(f"Draw blocks layer: {draw_blocks}")
        self.log.info(f"Draw walls layer: {draw_walls}")
        self.log.info(f"Draw liquids layer: {draw_liquids}")
        self.log.info(f"Draw wires layer: {draw_wires}")
        self.log.info(f"Draw paints: {draw_paint}")

        # If all layers are disabled, raise an Error
        if (
            draw_background is False
            and draw_blocks is False
            and draw_walls is False
            and draw_liquids is False
            and draw_wires is False
        ):
            raise ValueError("All layers are disabled")
            quit()

        self.log.info("Using TEdit Colors")
        colors = constants.DEFAULT_COLORS

        to_merge = []

        self.log.info(f'Parsing world from { self.config["world"]["file_path"] }...')
        world: lihzahrd.World = lihzahrd.World.create_from_file(
            self.config["world"]["file_path"]
        )
        min_x, min_y, max_x, max_y = self.get_region_size(
            world=world,
            min_x=min_x,
            min_y=min_y,
            region_width=region_width,
            region_height=region_height,
        )
        self.log.info(
            f"Rendering world coordinates between ({min_x}, {min_y}) to ({max_x}, {max_y}"
        )
        width = max_x - min_x
        height = max_y - min_y
        if draw_background:
            self.log.info("Drawing the background...")
            background = Image.new("RGBA", (width, height))
            draw = ImageDraw.Draw(background)
            curr_y = 0
            if min_y <= world.underground_level:
                sky_y = min(world.underground_level - min_y, height)
                draw.rectangle(
                    ((0, curr_y), (width, sky_y)),
                    tuple(colors["Globals"].get("Sky", (0, 0, 0, 0))),
                )
                curr_y = sky_y + 1
            if max_y > world.underground_level and min_y <= world.cavern_level:
                earth_y = min(world.cavern_level - min_y, height)
                draw.rectangle(
                    ((0, curr_y), (width, earth_y)),
                    tuple(colors["Globals"].get("Earth", (0, 0, 0, 0))),
                )
                curr_y = earth_y + 1
            edge_of_rock = world.size.y - 192
            if max_y > world.cavern_level and min_y <= edge_of_rock:
                rock_y = min(edge_of_rock - min_y, height)
                draw.rectangle(
                    ((0, curr_y), (width, rock_y)),
                    tuple(colors["Globals"].get("Rock", (0, 0, 0, 0))),
                )
                curr_y = rock_y + 1
            if max_y > edge_of_rock:
                draw.rectangle(
                    ((0, curr_y), (width, height)),
                    tuple(colors["Globals"].get("Hell", (0, 0, 0, 0))),
                )
            del draw
            to_merge.append(background)

        if draw_walls:
            self.log.info("Drawing walls...")
            walls = Image.new("RGBA", (width, height))
            draw = ImageDraw.Draw(walls)
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    tile = world.tiles[x, y]
                    if tile.wall:
                        if draw_paint and tile.wall.paint:
                            color = tuple(
                                colors["Paints"].get(str(tile.wall.paint), (0, 0, 0, 0))
                            )
                        else:
                            color = tuple(
                                colors["Walls"].get(
                                    str(tile.wall.type.value), (0, 0, 0, 0)
                                )
                            )
                        draw.point((x - min_x, y - min_y), color)
                if not x % 100:
                    self.log.info(f"{x} / {width} rows done")
            del draw
            to_merge.append(walls)

        if draw_liquids:
            self.log.info("Drawing liquids...")
            liquids = Image.new("RGBA", (width, height))
            draw = ImageDraw.Draw(liquids)
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    tile = world.tiles[x, y]
                    if tile.liquid:
                        if tile.liquid.type == lihzahrd.enums.LiquidType.WATER:
                            color = tuple(colors["Globals"].get("Water", (0, 0, 0, 0)))
                        elif tile.liquid.type == lihzahrd.enums.LiquidType.LAVA:
                            color = tuple(colors["Globals"].get("Lava", (0, 0, 0, 0)))
                        elif tile.liquid.type == lihzahrd.enums.LiquidType.HONEY:
                            color = tuple(colors["Globals"].get("Honey", (0, 0, 0, 0)))
                        else:
                            continue
                        draw.point((x - min_x, y - min_y), color)
                if not x % 100:
                    self.log.info(f"{x} / {width} rows done")
            del draw
            to_merge.append(liquids)

        if draw_blocks:
            self.log.info("Drawing blocks...")
            blocks = Image.new("RGBA", (width, height))
            draw = ImageDraw.Draw(blocks)
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    tile = world.tiles[x, y]
                    if tile.block:
                        if draw_paint and tile.block.paint:
                            color = tuple(
                                colors["Paints"].get(
                                    str(tile.block.paint), (0, 0, 0, 0)
                                )
                            )
                        else:
                            color = tuple(
                                colors["Blocks"].get(
                                    str(tile.block.type.value), (0, 0, 0, 0)
                                )
                            )
                        draw.point((x - min_x, y - min_y), color)
                if not x % 100:
                    self.log.info(f"{x} / {width} rows done")
            del draw
            to_merge.append(blocks)

        if draw_wires:
            self.log.info("Drawing wires...")
            wires = Image.new("RGBA", (width, height))
            draw = ImageDraw.Draw(wires)
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    tile = world.tiles[x, y]
                    if tile.wiring:
                        if tile.wiring.red:
                            color = tuple(colors["Globals"].get("Wire", (0, 0, 0, 0)))
                        elif tile.wiring.blue:
                            color = tuple(colors["Globals"].get("Wire1", (0, 0, 0, 0)))
                        elif tile.wiring.green:
                            color = tuple(colors["Globals"].get("Wire2", (0, 0, 0, 0)))
                        elif tile.wiring.yellow:
                            color = tuple(colors["Globals"].get("Wire3", (0, 0, 0, 0)))
                        else:
                            continue
                        draw.point((x - min_x, y - min_y), color)
                if not x % 100:
                    self.log.info(f"{x} / {width} rows done")
            del draw
            to_merge.append(wires)

        self.log.info("Merging layers...")
        final = Image.new("RGBA", (width, height))
        while to_merge:
            final = Image.alpha_composite(final, to_merge.pop(0))

        self.log.info("Saving image...")
        final.save(output_file)

        self.log.info("Done!")

    def get_region_size(
        self,
        *,
        world: lihzahrd.World,
        min_x: typing.Optional[int] = None,
        min_y: typing.Optional[int] = None,
        region_width: typing.Optional[int] = None,
        region_height: typing.Optional[int] = None,
    ):
        min_x = max(0, min_x or 0)
        min_y = max(0, min_y or 0)
        if region_width:
            max_x = min(world.size.x, (min_x or world.size.x) + region_width)
        else:
            max_x = world.size.x
        if region_height:
            max_y = min(world.size.y, (min_y or world.size.y) + region_height)
        else:
            max_y = world.size.y
        return min_x, min_y, max_x, max_y

    def generateDeepZoomData(self):
        input_image = self.config["output"]["file_path"]
        deepZoomMap = deepzoom.ImageCreator(
            tile_size=128,
            tile_overlap=2,
            tile_format="png",
            image_quality=1,
            resize_filter="bicubic",
        )
        output_image = input_image.replace(".png", ".dzi")
        deepZoomMap.create(input_image, output_image)


if __name__ == "__main__":
    terraMapper = TerraMapper()
