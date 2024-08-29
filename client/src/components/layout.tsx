import {
  ActionIcon,
  AppShell,
  Group,
  Title,
  useMantineColorScheme,
} from "@mantine/core";
import { PropsWithChildren } from "react";
import { IconMoon, IconSun } from "@tabler/icons-react";

export const Layout = ({ children }: PropsWithChildren) => {
  const { toggleColorScheme, colorScheme } = useMantineColorScheme();

  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Group justify="space-between" px="sm">
          <Title p={6}>NaptALED</Title>
          <ActionIcon
            variant="outline"
            aria-label="theme"
            onClick={toggleColorScheme}
          >
            {colorScheme === "dark" ? <IconSun /> : <IconMoon />}
          </ActionIcon>
        </Group>
      </AppShell.Header>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
};
