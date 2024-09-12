import { Loader, Title, Flex, Button } from "@mantine/core";
import { PlayableScript } from "./components/playable-script";
import { useScripts } from "./hooks/use-scripts";

export const Scripts = () => {
  const { scripts, isLoading, changeScript } = useScripts();
  if (isLoading || !scripts || !scripts.data) return <Loader />;

  return (
    <>
      <Title pb="sm">Scripts</Title>
      <Flex
        gap="md"
        justify="flex-start"
        align="flex-start"
        direction="row"
        wrap="wrap"
      >
        {scripts.data.scripts.map((script) => (
          <Button
            key={script.script_id}
            onClick={() => {
              changeScript(script.script_id);
            }}
            disabled={
              scripts.data.current_script.script_id === script.script_id
            }
          >
            {script.script_name.toUpperCase()}
          </Button>
        ))}
      </Flex>
      {scripts.data.current_script.is_playable && (
        <PlayableScript
          scriptId={scripts.data.current_script.script_id}
          scriptName={scripts.data.current_script.script_name}
        />
      )}
    </>
  );
};
