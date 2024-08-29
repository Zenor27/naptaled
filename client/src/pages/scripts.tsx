import { useMutation, useQuery, useQueryClient } from "react-query";
import { useCallback } from "react";
import { getScripts, postChangeScript } from "../api";
import { Button, Flex, Loader, Title } from "@mantine/core";

const useScripts = () => {
  const queryClient = useQueryClient();
  const { data: scripts, isLoading } = useQuery({
    queryKey: ["scripts"],
    queryFn: getScripts,
  });

  const { mutate } = useMutation({
    mutationFn: (script: string) => postChangeScript({ body: { script } }),
    onSuccess: () => {
      queryClient.invalidateQueries("scripts");
    },
  });

  const changeScript = useCallback(
    (script: string) => {
      mutate(script);
    },
    [mutate]
  );

  return { scripts, isLoading, changeScript };
};

export const Scripts = () => {
  const { scripts, isLoading, changeScript } = useScripts();
  if (isLoading || !scripts) return <Loader />;

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
        {scripts.data?.scripts.map((script) => (
          <Button
            key={script}
            onClick={() => {
              if (script === "display_text") changeScript(script);
            }}
            disabled={scripts.data?.current_script === script}
          >
            {script.replace(/_/g, " ").replace("display", "").toUpperCase()}
          </Button>
        ))}
      </Flex>
    </>
  );
};
